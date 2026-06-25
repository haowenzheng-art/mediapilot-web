"""
数据库配置
"""
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from backend.config.settings import settings

logger = logging.getLogger(__name__)

# 创建引擎（生产用 PostgreSQL 时启用连接池；SQLite 用静态池避免线程问题）
_is_sqlite = "sqlite" in settings.DATABASE_URL
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 1800,
}
if _is_sqlite:
    from sqlalchemy.pool import StaticPool
    engine_kwargs = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_timeout"] = 30

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# SQLite 开启 WAL 模式以提升并发
if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _):
        try:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        except Exception as e:
            logger.warning(f"SQLite pragma 设置失败: {e}")

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """数据库会话依赖注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """初始化数据库，创建所有表"""
    from backend.models.database.base import Base
    Base.metadata.create_all(bind=engine)


def dispose_engine() -> None:
    """应用关闭时释放连接池"""
    try:
        engine.dispose()
        logger.info("数据库连接池已释放")
    except Exception as e:
        logger.error(f"数据库连接池释放失败: {e}")


class TransactionManager:
    """事务管理器上下文类"""

    def __init__(self, db: Session):
        self.db = db
        self.in_transaction = False

    def __enter__(self):
        try:
            self.db.begin_nested()
            self.in_transaction = True
            return self
        except Exception:
            self.db.rollback()
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.in_transaction:
            try:
                if exc_type is None:
                    self.db.commit()
                else:
                    self.db.rollback()
            except Exception:
                self.db.rollback()
                raise

    def commit(self):
        if self.in_transaction:
            self.db.commit()

    def rollback(self):
        if self.in_transaction:
            self.db.rollback()
