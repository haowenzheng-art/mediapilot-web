"""
数据库配置
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# 从环境变量或配置读取
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./mediapilot.db"
)

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
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
    # 导入 Base 从 models.database.base
    from backend.models.database.base import Base
    Base.metadata.create_all(bind=engine)


class TransactionManager:
    """事务管理器上下文类"""

    def __init__(self, db: Session):
        """
        初始化事务管理器

        Args:
            db: 数据库会话
        """
        self.db = db
        self.in_transaction = False

    def __enter__(self):
        """
        进入事务上下文

        开始一个新事务
        """
        try:
            # 使用嵌套事务
            self.db.begin_nested()
            self.in_transaction = True
            return self
        except Exception as e:
            self.db.rollback()
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出事务上下文

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常回溯
        """
        if self.in_transaction:
            try:
                if exc_type is None:
                    # 没有异常，提交事务
                    self.db.commit()
                else:
                    # 有异常，回滚事务
                    self.db.rollback()
            except Exception:
                # 提交或回滚失败，确保数据库状态一致
                self.db.rollback()
                raise

    def commit(self):
        """手动提交事务"""
        if self.in_transaction:
            self.db.commit()

    def rollback(self):
        """手动回滚事务"""
        if self.in_transaction:
            self.db.rollback()
