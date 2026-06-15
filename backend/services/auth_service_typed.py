"""
认证授权业务逻辑
使用 Python 类型提示，遵循 PEP 8 标准
"""
import logging
import bcrypt
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.models.domain.user import UserCreate, UserLogin
from backend.models.database.tables import UserTable, TokenBlacklistTable
from backend.core.jwt import (
    create_access_token, create_refresh_token, decode_token,
    get_user_id_from_token, verify_token, hash_token
)

# 配额消耗配置
QUOTA_COSTS: Dict[str, int] = {
    "generate_script": 5,
    "rewrite_transcript": 5,
    "generate_outline": 3,
    "search_trending": 2,
    "search_competitors": 2,
    "transcribe_audio": 10,
    "transcribe_video": 10,
    "generate_copywriting": 5,
    "rewrite_copywriting": 3,
    "generate_shoot_script": 8,
    "create_subscription": 1,
}

DEFAULT_QUOTA: int = 100
MAX_QUOTA: int = 100000

logger = logging.getLogger(__name__)


class AuthService:
    """
    认证服务

    提供用户注册、登录、配额管理等功能
    """

    def __init__(self) -> None:
        """初始化服务"""
        pass

    @staticmethod
    def hash_password(password: str) -> str:
        """
        哈希密码

        Args:
            password: 明文密码

        Returns:
            str: 哈希后的密码
        """
        if not password:
            raise ValueError("密码不能为空")
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        验证密码

        Args:
            plain_password: 明文密码
            hashed_password: 哈希后的密码

        Returns:
            bool: 是否匹配
        """
        if not plain_password or not hashed_password:
            return False
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password if isinstance(hashed_password, bytes) else hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            return False

    @staticmethod
    def store_refresh_token(db: Session, refresh_token: str, user_id: int) -> TokenBlacklistTable:
        """存储刷新令牌哈希到黑名单表"""
        payload = decode_token(refresh_token, expected_type="refresh")
        expires_at = datetime.utcfromtimestamp(payload["exp"])

        token_entry = TokenBlacklistTable(
            token_hash=hash_token(refresh_token),
            user_id=user_id,
            expires_at=expires_at,
            is_revoked=False,
        )
        db.add(token_entry)
        db.commit()
        db.refresh(token_entry)
        return token_entry

    @staticmethod
    def validate_refresh_token(db: Session, refresh_token: str) -> Tuple[int, str]:
        """
        验证刷新令牌：JWT 有效性 + DB 是否存在且未撤销。

        Returns:
            (user_id, username)

        Raises:
            ValueError: 令牌无效、已撤销或不在已签发列表中
        """
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id = int(payload["sub"])
        username = payload.get("username", "")

        token_hash = hash_token(refresh_token)
        entry = db.query(TokenBlacklistTable).filter(
            TokenBlacklistTable.token_hash == token_hash,
            TokenBlacklistTable.is_revoked == False,
        ).first()

        if not entry:
            raise ValueError("刷新令牌无效: 令牌不在已签发列表中")
        if entry.is_revoked:
            raise ValueError("刷新令牌已撤销")
        if entry.expires_at < datetime.utcnow():
            raise ValueError("刷新令牌已过期")

        return entry.user_id, username

    @staticmethod
    def revoke_refresh_token(db: Session, refresh_token: str) -> bool:
        """撤销刷新令牌，返回是否成功找到并撤销"""
        token_hash = hash_token(refresh_token)
        entry = db.query(TokenBlacklistTable).filter(
            TokenBlacklistTable.token_hash == token_hash
        ).first()

        if not entry:
            return False

        entry.is_revoked = True
        db.commit()
        logger.info(f"刷新令牌已撤销: user_id={entry.user_id}")
        return True

    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> UserTable:
        """
        注册用户

        Args:
            db: 数据库会话
            user_data: 用户注册数据

        Returns:
            UserTable: 新创建的用户对象

        Raises:
            ValueError: 用户名或邮箱已存在
            IntegrityError: 数据库约束错误
        """
        # 检查用户名是否已存在
        existing_user = db.query(UserTable).filter(UserTable.username == user_data.username).first()
        if existing_user:
            logger.warning(f"注册失败: 用户名已存在 - {user_data.username}")
            raise ValueError("用户名已存在")

        # 检查邮箱是否已存在
        if user_data.email:
            existing_email = db.query(UserTable).filter(UserTable.email == user_data.email).first()
            if existing_email:
                logger.warning(f"注册失败: 邮箱已存在 - {user_data.email}")
                raise ValueError("邮箱已存在")

        # 创建新用户
        hashed_password = AuthService.hash_password(user_data.password)
        user = UserTable(
            username=user_data.username,
            password_hash=hashed_password,
            email=user_data.email,
            quota_balance=DEFAULT_QUOTA,
            is_active=True,
            is_admin=False
        )

        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"用户注册成功: {user_data.username}")
            return user
        except IntegrityError as e:
            db.rollback()
            logger.error(f"注册失败: 数据库错误 - {e}")
            raise

    @staticmethod
    def login_user(db: Session, login_data: UserLogin) -> Tuple[UserTable, str, str]:
        """
        用户登录

        Args:
            db: 数据库会话
            login_data: 登录数据

        Returns:
            Tuple[UserTable, str, str]: (用户对象, access_token, refresh_token)

        Raises:
            ValueError: 用户名、密码错误或账户被禁用
        """
        user = db.query(UserTable).filter(UserTable.username == login_data.username).first()

        if not user:
            logger.warning(f"登录失败: 用户名不存在 - {login_data.username}")
            raise ValueError("用户名或密码错误")

        if not AuthService.verify_password(login_data.password, user.password_hash):
            logger.warning(f"登录失败: 密码错误 - {login_data.username}")
            raise ValueError("用户名或密码错误")

        if not user.is_active:
            logger.warning(f"登录失败: 账户已被禁用 - {login_data.username}")
            raise ValueError("用户名或密码错误")

        # 生成 token
        token_data = {"sub": str(user.id), "username": user.username}
        token = create_access_token(data=token_data)
        refresh = create_refresh_token(data=token_data)

        # 存储刷新令牌哈希到黑名单表
        AuthService.store_refresh_token(db, refresh, user.id)

        logger.info(f"用户登录成功: {login_data.username}")

        return user, token, refresh

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[UserTable]:
        """
        根据 ID 获取用户

        Args:
            db: 数据库会话
            user_id: 用户 ID

        Returns:
            Optional[UserTable]: 用户对象或 None
        """
        return db.query(UserTable).filter(UserTable.id == user_id).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[UserTable]:
        """
        根据用户名获取用户

        Args:
            db: 数据库会话
            username: 用户名

        Returns:
            Optional[UserTable]: 用户对象或 None
        """
        return db.query(UserTable).filter(UserTable.username == username).first()

    @staticmethod
    def get_user_from_token(db: Session, token: str) -> Optional[UserTable]:
        """
        从 token 获取用户

        Args:
            db: 数据库会话
            token: JWT token

        Returns:
            Optional[UserTable]: 用户对象或 None
        """
        try:
            user_id = get_user_id_from_token(token)
            return AuthService.get_user_by_id(db, user_id)
        except Exception as e:
            logger.error(f"从 token 获取用户失败: {e}")
            return None

    @staticmethod
    def check_quota(db: Session, user_id: int, feature: str) -> Tuple[bool, int]:
        """
        检查用户配额是否足够

        Args:
            db: 数据库会话
            user_id: 用户 ID
            feature: 功能名称

        Returns:
            Tuple[bool, int]: (是否足够, 当前余额)
        """
        user = AuthService.get_user_by_id(db, user_id)
        if not user:
            return False, 0

        cost = QUOTA_COSTS.get(feature, 1)
        return user.quota_balance >= cost, user.quota_balance

    @staticmethod
    def deduct_quota(db: Session, user_id: int, feature: str) -> Tuple[bool, int]:
        """
        扣减用户配额

        Args:
            db: 数据库会话
            user_id: 用户 ID
            feature: 功能名称

        Returns:
            Tuple[bool, int]: (是否成功, 新余额)
        """
        user = AuthService.get_user_by_id(db, user_id)
        if not user:
            return False, 0

        cost = QUOTA_COSTS.get(feature, 1)
        if user.quota_balance < cost:
            logger.warning(f"扣减配额失败: 余额不足 - 用户ID:{user_id}, 余额:{user.quota_balance}, 需要:{cost}")
            return False, user.quota_balance

        user.quota_balance -= cost
        db.commit()
        db.refresh(user)
        logger.info(f"扣减配额成功: 用户ID:{user_id}, 操作:{feature}, 新余额:{user.quota_balance}")
        return True, user.quota_balance

    @staticmethod
    def recharge_quota(
        db: Session,
        user_id: int,
        amount: int,
        is_admin_request: bool = False
    ) -> Tuple[bool, int, int]:
        """
        充值配额

        Args:
            db: 数据库会话
            user_id: 用户 ID
            amount: 充值金额
            is_admin_request: 是否为管理员请求

        Returns:
            Tuple[bool, int, int]: (是否成功, 旧余额, 新余额)
        """
        user = AuthService.get_user_by_id(db, user_id)
        if not user:
            return False, 0, 0

        old_balance = user.quota_balance
        new_balance = old_balance + amount

        # 检查是否超过限制（管理员可以超过）
        if not is_admin_request and new_balance > MAX_QUOTA:
            logger.warning(f"充值失败: 超过最大配额 - 新余额:{new_balance}")
            return False, old_balance, old_balance

        user.quota_balance = new_balance
        db.commit()
        db.refresh(user)
        logger.info(f"充值成功: 用户ID:{user_id}, 充值:{amount}, 新余额:{new_balance}")
        return True, old_balance, new_balance

    @staticmethod
    def get_quota_balance(db: Session, user_id: int) -> int:
        """
        获取配额余额

        Args:
            db: 数据库会话
            user_id: 用户 ID

        Returns:
            int: 配额余额
        """
        user = AuthService.get_user_by_id(db, user_id)
        return user.quota_balance if user else 0

    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> bool:
        """
        禁用用户

        Args:
            db: 数据库会话
            user_id: 用户 ID

        Returns:
            bool: 是否成功
        """
        user = AuthService.get_user_by_id(db, user_id)
        if not user:
            return False

        user.is_active = False
        db.commit()
        db.refresh(user)
        logger.info(f"用户已禁用: 用户ID:{user_id}")
        return True

    @staticmethod
    def activate_user(db: Session, user_id: int) -> bool:
        """
        激活用户

        Args:
            db: 数据库会话
            user_id: 用户 ID

        Returns:
            bool: 是否成功
        """
        user = AuthService.get_user_by_id(db, user_id)
        if not user:
            return False

        user.is_active = True
        db.commit()
        db.refresh(user)
        logger.info.info(f"用户已激活: 用户ID:{user_id}")
        return True

    @staticmethod
    def get_all_users(db: Session) -> List[UserTable]:
        """
        获取所有用户列表

        Args:
            db: 数据库会话

        Returns:
            List[UserTable]: 用户列表
        """
        return db.query(UserTable).all()


# 创建全局服务实例
auth_service = AuthService()
