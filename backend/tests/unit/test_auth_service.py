"""
认证服务单元测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.services.auth_service import auth_service
from backend.models.domain.user import UserCreate, UserLogin
from backend.models.database.tables import UserTable, Base


# 使用内存数据库
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestAuthService:
    """认证服务测试"""

    def test_hash_password(self):
        """测试密码哈希"""
        password = "test123456"
        hashed = auth_service.hash_password(password)

        # 哈希后的密码不应等于明文
        assert hashed != password
        # 哈希后长度应大于明文
        assert len(hashed) > len(password)

    def test_verify_password_correct(self):
        """测试密码验证（正确密码）"""
        password = "test123456"
        hashed = auth_service.hash_password(password)

        result = auth_service.verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self):
        """测试密码验证（错误密码）"""
        password = "test123456"
        hashed = auth_service.hash_password(password)

        result = auth_service.verify_password("wrongpassword", hashed)
        assert result is False

    def test_register_user_success(self, db_session):
        """测试用户注册（成功）"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test@example.com"
        )

        user = auth_service.register_user(db_session, user_data)

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.quota_balance == auth_service.DEFAULT_QUOTA
        assert user.is_active is True
        assert user.is_admin is False
        assert user.id is not None

    def test_register_user_duplicate_username(self, db_session):
        """测试用户注册（用户名已存在）"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test1@example.com"
        )

        # 第一次注册成功
        auth_service.register_user(db_session, user_data)

        # 第二次注册应失败
        user_data2 = UserCreate(
            username="testuser",
            password="test123456",
            email="test2@example.com"
        )

        with pytest.raises(ValueError, match="用户名已存在"):
            auth_service.register_user(db_session, user_data2)

    def test_register_user_duplicate_email(self, db_session):
        """测试用户注册（邮箱已存在）"""
        user_data = UserCreate(
            username="testuser1",
            password="test123456",
            email="test@example.com"
        )

        # 第一次注册成功
        auth_service.register_user(db_session, user_data)

        # 第二次注册应失败
        user_data2 = UserCreate(
            username="testuser2",
            password="test123456",
            email="test@example.com"
        )

        with pytest.raises(ValueError, match="邮箱已存在"):
            auth_service.register_user(db_session, user_data2)

    def test_login_user_success(self, db_session):
        """测试用户登录（成功）"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test@example.com"
        )
        auth_service.register_user(db_session, user_data)

        login_data = UserLogin(username="testuser", password="test123456")
        user, token = auth_service.login_user(db_session, login_data)

        assert user.username == "testuser"
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_login_user_wrong_password(self, db_session):
        """测试用户登录（错误密码）"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test@example.com"
        )
        auth_service.register_user(db_session, user_data)

        login_data = UserLogin(username="testuser", password="wrongpassword")

        with pytest.raises(ValueError, match="用户名或密码错误"):
            auth_service.login_user(db_session, login_data)

    def test_login_user_not_exists(self, db_session):
        """测试用户登录（用户不存在）"""
        login_data = UserLogin(username="nonexistent", password="test123456")

        with pytest.raises(ValueError, match="用户名或密码错误"):
            auth_service.login_user(db_session, login_data)

    def test_login_user_disabled(self, db_session):
        """测试用户登录（用户已禁用）"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test@example.com"
        )
        user = auth_service.register_user(db_session, user_data)

        # 禁用用户
        user.is_active = False
        db_session.commit()

        login_data = UserLogin(username="testuser", password="test123456")

        with pytest.raises(ValueError, match="用户已被禁用"):
            auth_service.login_user(db_session, login_data)

    def test_get_user_by_id(self, db_session):
        """测试根据 ID 获取用户"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test@example.com"
        )
        created_user = auth_service.register_user(db_session, user_data)

        user = auth_service.get_user_by_id(db_session, created_user.id)

        assert user is not None
        assert user.username == "testuser"

    def test_get_user_by_username(self, db_session):
        """测试根据用户名获取用户"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test@example.com"
        )
        auth_service.register_user(db_session, user_data)

        user = auth_service.get_user_by_username(db_session, "testuser")

        assert user is not None
        assert user.username == "testuser"

    def test_check_quota_sufficient(self, db_session):
        """测试配额检查（余额足够）"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test@example.com"
        )
        user = auth_service.register_user(db_session, user_data)

        result = auth_service.check_quota(db_session, user.id, "generate_script")

        assert result is True

    def test_check_quota_insufficient(self, db_session):
        """测试配额检查（余额不足）"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test@example.com"
        )
        user = auth_service.register_user(db_session, user_data)

        # 设置余额为 0
        user.quota_balance = 0
        db_session.commit()

        result = auth_service.check_quota(db_session, user.id, "generate_script")

        assert result is False

    def test_deduct_quota_success(self, db_session):
        """测试配额扣减（成功）"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test@example.com"
        )
        user = auth_service.register_user(db_session, user_data)
        initial_balance = user.quota_balance

        success, balance = auth_service.deduct_quota(db_session, user.id, "generate_script")

        assert success is True
        assert balance == initial_balance - auth_service.QUOTA_COSTS["generate_script"]

    def test_deduct_quota_insufficient(self, db_session):
        """测试配额扣减（余额不足）"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test@example.com"
        )
        user = auth_service.register_user(db_session, user_data)
        user.quota_balance = 0
        db_session.commit()

        success, balance = auth_service.deduct_quota(db_session, user.id, "generate_script")

        assert success is False
        assert balance == 0

    def test_recharge_quota(self, db_session):
        """测试配额充值"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test@example.com"
        )
        user = auth_service.register_user(db_session, user_data)
        initial_balance = user.quota_balance
        recharge_amount = 50

        success, old_balance, new_balance = auth_service.recharge_quota(
            db_session, user.id, recharge_amount
        )

        assert success is True
        assert old_balance == initial_balance
        assert new_balance == initial_balance + recharge_amount

    def test_recharge_quota_limit(self, db_session):
        """测试配额充值（超过限制）"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test@example.com"
        )
        user = auth_service.register_user(db_session, user_data)

        # 尝试充值超过限制（100000）
        success, old_balance, new_balance = auth_service.recharge_quota(
            db_session, user.id, 200000, is_admin_request=False
        )

        assert success is False

    def test_recharge_quota_admin_override(self, db_session):
        """测试配额充值（管理员可超过限制）"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test@example.com"
        )
        user = auth_service.register_user(db_session, user_data)
        initial_balance = user.quota_balance

        # 管理员可以充值超过限制
        success, old_balance, new_balance = auth_service.recharge_quota(
            db_session, user.id, 200000, is_admin_request=True
        )

        assert success is True
        assert new_balance == initial_balance + 200000

    def test_get_quota_balance(self, db_session):
        """测试获取配额余额"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test@example.com"
        )
        user = auth_service.register_user(db_session, user_data)

        balance = auth_service.get_quota_balance(db_session, user.id)

        assert balance == auth_service.DEFAULT_QUOTA

    def test_deactivate_user(self, db_session):
        """测试禁用用户"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test@example.com"
        )
        user = auth_service.register_user(db_session, user_data)

        success = auth_service.deactivate_user(db_session, user.id)

        assert success is True
        db_session.refresh(user)
        assert user.is_active is False

    def test_activate_user(self, db_session):
        """测试激活用户"""
        user_data = UserCreate(
            username="testuser",
            password="test123456",
            email="test@example.com"
        )
        user = auth_service.register_user(db_session, user_data)
        user.is_active = False
        db_session.commit()

        success = auth_service.activate_user(db_session, user.id)

        assert success is True
        db_session.refresh(user)
        assert user.is_active is True

    def test_quota_costs_config(self):
        """测试配额消耗配置"""
        assert auth_service.QUOTA_COSTS["generate_script"] == 5
        assert auth_service.QUOTA_COSTS["rewrite_transcript"] == 5
        assert auth_service.QUOTA_COSTS["generate_outline"] == 3
        assert auth_service.QUOTA_COSTS["search_trending"] == 2
        assert auth_service.QUOTA_COSTS["search_competitors"] == 2
        assert auth_service.QUOTA_COSTS["transcribe_audio"] == 10
        assert auth_service.QUOTA_COSTS["transcribe_video"] == 10
