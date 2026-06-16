"""
数据库配置
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from backend.config.settings import settings

# 创建引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    数据库会话依赖注入

    用法:
        def some_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建所有表"""
    from backend.models.database.base import Base
    Base.metadata.create_all(bind=engine)


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
        except Exception as e:
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
