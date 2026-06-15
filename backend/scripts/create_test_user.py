"""
创建测试用户并获取 token

用法:
    # 从项目根目录运行
    python -m backend.scripts.create_test_user

    # 或直接运行
    python backend/scripts/create_test_user.py
"""
import os
import sys

# 确保项目根目录在 sys.path 中
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.config.database import SessionLocal, init_db
from backend.services.auth_service import auth_service
from backend.models.domain.user import UserCreate, UserLogin

USERNAME = "testuser"
PASSWORD = "testpass123"
TOKEN_FILE = os.path.join(project_root, "test_token.txt")


def create_test_user():
    init_db()
    db = SessionLocal()
    try:
        # 注册
        try:
            user = auth_service.register_user(db, UserCreate(username=USERNAME, password=PASSWORD))
            print(f"[OK] 用户注册成功: {user.username} (id={user.id})")
        except ValueError as e:
            if "已存在" in str(e):
                print(f"[SKIP] 用户已存在: {USERNAME}")
            else:
                raise

        # 登录 — 如果失败（密码不匹配），删除旧用户并重建
        try:
            user, token = auth_service.login_user(db, UserLogin(username=USERNAME, password=PASSWORD))
        except ValueError:
            print(f"[FIX] 密码不匹配，重建用户: {USERNAME}")
            from backend.models.database.tables import UserTable
            db.query(UserTable).filter(UserTable.username == USERNAME).delete()
            db.commit()
            user = auth_service.register_user(db, UserCreate(username=USERNAME, password=PASSWORD))
            token = auth_service.login_user(db, UserLogin(username=USERNAME, password=PASSWORD))[1]

        print(f"[OK] 登录成功: {user.username}")

        # 保存 token
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(token)
        print(f"[OK] Token 已保存到: {TOKEN_FILE}")

        # 输出 token
        print(f"\naccess_token: {token}")
        return token
    except Exception as e:
        print(f"[FAIL] {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    create_test_user()
