"""
认证授权业务逻辑
"""
import bcrypt
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.models.domain.user import UserCreate, UserLogin
from backend.models.database.tables import UserTable
from backend.core.jwt import create_access_token, get_user_id_from_token, verify_token


class AuthService:
    """认证服务"""

    # 配额消耗配置
    QUOTA_COSTS = {
        "generate_script": 5,
        "rewrite_transcript": 5,
        "generate_outline": 3,
        "search_trending": 2,
        "transcribe_audio": 10,
        "transcribe_video": 10,
    }

    # 默认配额
    DEFAULT_QUOTA = 100

    # 最大配额限制
    MAX_QUOTA = 100000

    def __init__(self):
        pass

    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    def register_user(self, db: Session, user_data: UserCreate) -> UserTable:
        """注册用户"""
        # 检查用户名是否已存在
        existing_user = db.query(UserTable).filter(UserTable.username == user_data.username).first()
        if existing_user:
            raise ValueError("用户名已存在")

        # 检查邮箱是否已存在
        if user_data.email:
            existing_email = db.query(UserTable).filter(UserTable.email == user_data.email).first()
            if existing_email:
                raise ValueError("邮箱已存在")

        # 创建新用户
        hashed_password = self.hash_password(user_data.password)
        user = UserTable(
            username=user_data.username,
            password_hash=hashed_password,
            email=user_data.email,
            quota_balance=self.DEFAULT_QUOTA,
            is_active=True,
            is_admin=False
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    def login_user(self, db: Session, login_data: UserLogin) -> Tuple[UserTable, str]:
        """用户登录"""
        user = db.query(UserTable).filter(UserTable.username == login_data.username).first()

        if not user:
            raise ValueError("用户名或密码错误")

        if not self.verify_password(login_data.password, user.password_hash):
            raise ValueError("用户名或密码错误")

        if not user.is_active:
            raise ValueError("用户已被禁用")

        # 生成 token
        token = create_access_token(data={"sub": str(user.id), "username": user.username})

        return user, token

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[UserTable]:
        """根据 ID 获取用户"""
        return db.query(UserTable).filter(UserTable.id == user_id).first()

    def get_user_by_username(self, db: Session, username: str) -> Optional[UserTable]:
        """根据用户名获取用户"""
        return db.query(UserTable).filter(UserTable.username == username).first()

    def get_user_from_token(self, db: Session, token: str) -> Optional[UserTable]:
        """从 token 获取用户"""
        try:
            user_id = get_user_id_from_token(token)
            return self.get_user_by_id(db, user_id)
        except Exception:
            return None

    def check_quota(self, db: Session, user_id: int, feature: str) -> bool:
        """检查配额是否足够"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False

        cost = self.QUOTA_COSTS.get(feature, 1)
        return user.quota_balance >= cost

    def deduct_quota(self, db: Session, user_id: int, feature: str) -> Tuple[bool, int]:
        """扣减配额"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False, 0

        cost = self.QUOTA_COSTS.get(feature, 1)
        if user.quota_balance < cost:
            return False, user.quota_balance

        user.quota_balance -= cost
        db.commit()
        db.refresh(user)

        return True, user.quota_balance

    def recharge_quota(self, db: Session, user_id: int, amount: int, is_admin_request: bool = False) -> Tuple[bool, int, int]:
        """充值配额"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False, 0, 0

        old_balance = user.quota_balance
        new_balance = old_balance + amount

        # 检查是否超过限制（管理员可以超过）
        if not is_admin_request and new_balance > self.MAX_QUOTA:
            return False, old_balance, old_balance

        user.quota_balance = new_balance
        db.commit()
        db.refresh(user)

        return True, old_balance, new_balance

    def get_quota_balance(self, db: Session, user_id: int) -> int:
        """获取配额余额"""
        user = self.get_user_by_id(db, user_id)
        return user.quota_balance if user else 0

    def deactivate_user(self, db: Session, user_id: int) -> bool:
        """禁用用户"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False

        user.is_active = False
        db.commit()
        return True

    def activate_user(self, db: Session, user_id: int) -> bool:
        """激活用户"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False

        user.is_active = True
        db.commit()
        return True

    def get_all_users(self, db: Session) -> list[UserTable]:
        """获取所有用户列表"""
        return db.query(UserTable).all()


# 创建全局实例
auth_service = AuthService()
