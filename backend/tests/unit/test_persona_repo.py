"""
BE-015 人设数据模型 — Repository LRU 行为单元测试

验证：
- 最近 3 条上限
- 相同描述不重复创建（触发更新 last_used_at）
- 排序按 last_used_at desc
- 超过 3 条时删除最旧
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.models.database.tables import Base, UserTable
from backend.repository.persona_repo import PersonaRepository


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    user = UserTable(username="persona_test", password_hash="x", email="p@t.com")
    session.add(user)
    session.commit()
    session.refresh(user)
    yield session, user.id
    session.close()


class TestPersonaRepositoryLRU:
    def test_create_first_persona(self, db):
        session, uid = db
        repo = PersonaRepository(session)
        p = repo.create(uid, "幽默博主")
        assert p.id is not None
        assert p.persona_description == "幽默博主"
        assert len(repo.get_user_personas(uid)) == 1

    def test_at_most_three_personas(self, db):
        session, uid = db
        repo = PersonaRepository(session)
        for desc in ["A", "B", "C", "D", "E"]:
            repo.create(uid, desc)
        personas = repo.get_user_personas(uid)
        assert len(personas) == 3
        # 最新 3 条 = 最后插入的 C/D/E
        descs = {p.persona_description for p in personas}
        assert descs == {"C", "D", "E"}

    def test_duplicate_description_updates_instead_of_inserting(self, db):
        session, uid = db
        repo = PersonaRepository(session)
        first = repo.create(uid, "学者风")
        original_created = first.created_at
        # 重复创建应返回同一条并刷新 last_used_at
        again = repo.create(uid, "学者风")
        assert again.id == first.id
        assert again.created_at == original_created
        assert again.last_used_at >= original_created
        assert len(repo.get_user_personas(uid)) == 1

    def test_ordering_by_last_used_desc(self, db):
        session, uid = db
        repo = PersonaRepository(session)
        repo.create(uid, "X")
        repo.create(uid, "Y")
        repo.create(uid, "Z")
        # 推进时间，避免 4 次操作落进同一微秒导致 last_used_at 全等
        import time
        time.sleep(0.01)
        # 重新触达 X，应回到第一位
        repo.update_last_used(repo.get_by_description(uid, "X"))
        personas = repo.get_user_personas(uid)
        assert personas[0].persona_description == "X"

    def test_delete_persona(self, db):
        session, uid = db
        repo = PersonaRepository(session)
        p = repo.create(uid, "to_delete")
        assert repo.delete(p.id) is True
        assert repo.delete(p.id) is False  # 已删
        assert repo.get_user_personas(uid) == []

    def test_user_isolation(self, db):
        session, uid = db
        repo = PersonaRepository(session)
        # 第二个用户
        u2 = UserTable(username="other", password_hash="x", email="o@t.com")
        session.add(u2)
        session.commit()
        session.refresh(u2)

        repo.create(uid, "user1_persona")
        repo.create(u2.id, "user2_persona")
        assert len(repo.get_user_personas(uid)) == 1
        assert repo.get_user_personas(uid)[0].persona_description == "user1_persona"
        assert len(repo.get_user_personas(u2.id)) == 1
        assert repo.get_user_personas(u2.id)[0].persona_description == "user2_persona"
