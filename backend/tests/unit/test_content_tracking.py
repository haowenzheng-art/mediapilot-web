"""
内容关联单元测试
测试 ContentLibraryRepository 和 HotTopicTrendRepository
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.repository.content_library_repo import ContentLibraryRepository, HotTopicTrendRepository
from backend.models.database.tables import ContentTable, HotTopicTrendTable


class TestContentLibraryRepository:
    """内容库数据访问测试"""

    @pytest.fixture
    def repo(self, db_setup):
        """创建内容仓库"""
        from backend.tests.conftest import TestSessionLocal
        db = TestSessionLocal()
        return ContentLibraryRepository(db)

    @pytest.fixture
    def test_user(self, db_setup):
        """创建测试用户"""
        from backend.tests.conftest import TestSessionLocal
        from backend.models.database.tables import UserTable

        db = TestSessionLocal()
        user = UserTable(
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            quota_balance=100,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def test_create_content(self, repo, test_user):
        """测试创建内容记录"""
        content = repo.create(
            user_id=test_user.id,
            content_type="copywriting",
            content_uuid="copy-001",
            title="测试文案",
            summary="这是一个测试文案",
            mode="hotspot",
            persona="幽默风趣",
            platform="douyin",
            style="professional",
            hot_topic_id="topic-001",
            hot_topic_title="测试热点",
            hot_topic_source="抖音"
        )

        assert content.id is not None
        assert content.content_type == "copywriting"
        assert content.content_id == "copy-001"
        assert content.title == "测试文案"
        assert content.hot_topic_id == "topic-001"
        assert content.is_processed is False

    def test_create_content_with_shoot_script(self, repo, test_user):
        """测试创建拍摄脚本内容"""
        content = repo.create(
            user_id=test_user.id,
            content_type="shoot_script",
            content_uuid="script-001",
            title="拍摄脚本",
            summary="这是一个拍摄脚本",
            platform="xiaohongshu",
            style="humor"
        )

        assert content.id is not None
        assert content.content_type == "shoot_script"
        assert content.platform == "xiaohongshu"
        assert content.style == "humor"

    def test_get_content_by_id(self, repo, test_user):
        """测试根据ID获取内容"""
        # 先创建内容
        created = repo.create(
            user_id=test_user.id,
            content_type="copywriting",
            content_uuid="copy-002",
            title="测试文案2"
        )

        # 查询内容
        content = repo.get_by_id(created.id)
        assert content is not None
        assert content.id == created.id
        assert content.title == "测试文案2"

    def test_get_content_by_user(self, repo, test_user):
        """测试获取用户的内容列表"""
        # 创建多个内容
        repo.create(
            user_id=test_user.id,
            content_type="copywriting",
            content_uuid="copy-003",
            title="文案1"
        )
        repo.create(
            user_id=test_user.id,
            content_type="shoot_script",
            content_uuid="script-002",
            title="脚本1"
        )
        repo.create(
            user_id=test_user.id,
            content_type="copywriting",
            content_uuid="copy-004",
            title="文案2"
        )

        # 查询用户内容
        contents = repo.get_user_contents(test_user.id)
        assert len(contents) == 3
        assert all(c.user_id == test_user.id for c in contents)

    def test_get_content_by_user_and_type(self, repo, test_user):
        """测试根据用户和内容类型获取内容"""
        # 创建不同类型的内容
        repo.create(
            user_id=test_user.id,
            content_type="copywriting",
            content_uuid="copy-005",
            title="文案1"
        )
        repo.create(
            user_id=test_user.id,
            content_type="shoot_script",
            content_uuid="script-003",
            title="脚本1"
        )
        repo.create(
            user_id=test_user.id,
            content_type="copywriting",
            content_uuid="copy-006",
            title="文案2"
        )

        # 查询文案类型
        copywritings = repo.get_user_contents(test_user.id, content_type="copywriting")
        assert len(copywritings) == 2
        assert all(c.content_type == "copywriting" for c in copywritings)

        # 查询脚本类型
        scripts = repo.get_user_contents(test_user.id, content_type="shoot_script")
        assert len(scripts) == 1
        assert scripts[0].content_type == "shoot_script"

    def test_get_content_by_hot_topic(self, repo, test_user):
        """测试根据热点话题获取内容"""
        # 创建关联同一热点的内容
        repo.create(
            user_id=test_user.id,
            content_type="copywriting",
            content_uuid="copy-007",
            title="文案1",
            hot_topic_id="topic-002"
        )
        repo.create(
            user_id=test_user.id,
            content_type="shoot_script",
            content_uuid="script-004",
            title="脚本1",
            hot_topic_id="topic-002"
        )
        repo.create(
            user_id=test_user.id,
            content_type="copywriting",
            content_uuid="copy-008",
            title="其他文案",
            hot_topic_id="topic-003"
        )

        # 查询关联特定热点的内容
        contents = repo.get_hot_topic_contents("topic-002", test_user.id)
        assert len(contents) == 2
        assert all(c.hot_topic_id == "topic-002" for c in contents)

    def test_get_unprocessed_content(self, repo, test_user):
        """测试获取未处理的内容"""
        # 创建内容
        content1 = repo.create(
            user_id=test_user.id,
            content_type="copywriting",
            content_uuid="copy-009",
            title="未处理内容1"
        )
        content2 = repo.create(
            user_id=test_user.id,
            content_type="copywriting",
            content_uuid="copy-010",
            title="未处理内容2"
        )

        # 标记一个为已处理
        repo.mark_as_processed(content2.id)

        # 查询未处理内容
        unprocessed = repo.get_user_contents(test_user.id, is_processed=False)
        assert len(unprocessed) >= 1
        assert all(not c.is_processed for c in unprocessed)

    def test_mark_as_processed(self, repo, test_user):
        """测试标记内容为已处理"""
        # 创建内容
        content = repo.create(
            user_id=test_user.id,
            content_type="copywriting",
            content_id="copy-011",
            title="待处理内容"
        )

        assert content.is_processed is False
        assert content.processed_at is None

        # 标记为已处理
        updated = repo.mark_as_processed(content.id)

        assert updated.is_processed is True
        assert updated.processed_at is not None
        assert isinstance(updated.processed_at, datetime)

    def test_update_content(self, repo, test_user):
        """测试更新内容"""
        # 创建内容
        content = repo.create(
            user_id=test_user.id,
            content_type="copywriting",
            content_uuid="copy-012",
            title="原标题",
            summary="原摘要"
        )

        # 更新内容
        updated = repo.update(
            content,
            title="更新后的标题",
            summary="更新后的摘要"
        )

        assert updated.title == "更新后的标题"
        assert updated.summary == "更新后的摘要"

    def test_delete_content(self, repo, test_user):
        """测试删除内容"""
        # 创建内容
        content = repo.create(
            user_id=test_user.id,
            content_type="copywriting",
            content_id="copy-013",
            title="待删除内容"
        )

        content_id = content.id

        # 删除内容
        result = repo.delete(content_id)
        assert result is True

        # 验证删除
        deleted_content = repo.get_by_id(content_id)
        assert deleted_content is None

    def test_get_content_count_by_user(self, repo, test_user):
        """测试获取用户内容数量统计"""
        # 创建内容
        repo.create(
            user_id=test_user.id,
            content_type="copywriting",
            content_uuid="copy-015",
            title="文案1"
        )
        repo.create(
            user_id=test_user.id,
            content_type="copywriting",
            content_uuid="copy-016",
            title="文案2"
        )

        # 统计数量
        count = repo.count_user_contents(test_user.id)
        assert count >= 2

    def test_get_content_by_uuid(self, repo, test_user):
        """测试根据UUID获取内容"""
        # 创建内容
        repo.create(
            user_id=test_user.id,
            content_type="copywriting",
            content_uuid="copy-017",
            title="UUID测试"
        )

        # 查询内容
        content = repo.get_by_content_id("copywriting", "copy-017")
        assert content is not None
        assert content.content_id == "copy-017"
        assert content.title == "UUID测试"

    def test_pagination(self, repo, test_user):
        """测试分页查询"""
        # 创建多个内容
        for i in range(15):
            repo.create(
                user_id=test_user.id,
                content_type="copywriting",
                content_uuid=f"copy-{i:03d}",
                title=f"标题{i}"
            )

        # 分页查询
        page1 = repo.get_user_contents(test_user.id, limit=10, offset=0)
        page2 = repo.get_user_contents(test_user.id, limit=10, offset=10)

        assert len(page1) == 10
        assert len(page2) == 5
        assert len(set([c.id for c in page1]).intersection(set([c.id for c in page2]))) == 0


class TestHotTopicTrendRepository:
    """热点趋势数据访问测试"""

    @pytest.fixture
    def repo(self, db_setup):
        """创建趋势仓库"""
        from backend.tests.conftest import TestSessionLocal
        db = TestSessionLocal()
        from backend.repository.content_repo import HotTopicTrendRepository
        return HotTopicTrendRepository(db)

    def test_create_trend_record(self, repo):
        """测试创建趋势记录"""
        trend = repo.create(
            hot_topic_id="topic-001",
            hot_topic_title="测试热点",
            hot_topic_source="抖音",
            heat_score=1000,
            trend_direction="up"
        )

        assert trend.id is not None
        assert trend.hot_topic_id == "topic-001"
        assert trend.heat_score == 1000
        assert trend.trend_direction == "up"

    def test_create_trend_record_with_down_direction(self, repo):
        """测试创建下降趋势记录"""
        trend = repo.create(
            hot_topic_id="topic-002",
            hot_topic_title="下降热点",
            hot_topic_source="微博",
            heat_score=800,
            trend_direction="down"
        )

        assert trend.trend_direction == "down"
        assert trend.heat_score == 800

    def test_create_trend_record_with_stable_direction(self, repo):
        """测试创建平稳趋势记录"""
        trend = repo.create(
            hot_topic_id="topic-003",
            hot_topic_title="平稳热点",
            hot_topic_source="知乎",
            heat_score=500,
            trend_direction="stable"
        )

        assert trend.trend_direction == "stable"
        assert trend.heat_score == 500

    def test_get_trends_by_topic_id(self, repo):
        """测试获取话题的趋势历史"""
        # 创建多个趋势记录
        now = datetime.utcnow()
        repo.create(
            hot_topic_id="topic-004",
            hot_topic_title="追踪热点",
            heat_score=1000,
            trend_direction="up"
        )
        repo.create(
            hot_topic_id="topic-004",
            hot_topic_title="追踪热点",
            heat_score=1200,
            trend_direction="up"
        )
        repo.create(
            hot_topic_id="topic-005",
            hot_topic_title="其他热点",
            heat_score=800,
            trend_direction="down"
        )

        # 查询特定话题的趋势
        trends = repo.get_by_topic_id("topic-004")
        assert len(trends) == 2
        assert all(t.hot_topic_id == "topic-004" for t in trends)

    def test_get_latest_trend_by_topic(self, repo):
        """测试获取话题的最新趋势"""
        # 创建趋势记录
        repo.create(
            hot_topic_id="topic-006",
            hot_topic_title="最新热点",
            heat_score=900,
            trend_direction="up"
        )
        latest = repo.create(
            hot_topic_id="topic-006",
            hot_topic_title="最新热点",
            heat_score=1100,
            trend_direction="up"
        )

        # 获取最新趋势
        trends = repo.get_topic_trends("topic-006", limit=1)
        assert len(trends) == 1
        assert trends[0].heat_score == 1100
        assert trends[0].id == latest.id

    def test_get_trends_by_date_range(self, repo):
        """测试根据日期范围获取趋势"""
        # 创建趋势记录
        repo.create(
            hot_topic_id="topic-007",
            hot_topic_title="日期范围热点",
            heat_score=700,
            trend_direction="up"
        )

        # 查询最近的趋势（24小时内）
        trends = repo.get_recent_trends(hours=24)
        assert len(trends) >= 1

    def test_batch_create_trends(self, repo):
        """测试批量创建趋势记录"""
        # 批量创建
        trends_data = [
            {"hot_topic_id": "topic-008", "hot_topic_title": "热点1", "heat_score": 1000, "trend_direction": "up"},
            {"hot_topic_id": "topic-009", "hot_topic_title": "热点2", "heat_score": 900, "trend_direction": "down"},
            {"hot_topic_id": "topic-010", "hot_topic_title": "热点3", "heat_score": 800, "trend_direction": "stable"},
        ]

        count = repo.batch_create(trends_data)
        assert count == 3

    def test_delete_old_trends(self, repo):
        """测试删除旧的趋势记录"""
        # 创建趋势记录
        repo.create(
            hot_topic_id="topic-011",
            hot_topic_title="旧热点",
            heat_score=600,
            trend_direction="stable"
        )

        # 删除30天前的趋势（不会删除刚创建的）
        count = repo.delete_old_trends(days=30)
        assert count == 0

        # 所有趋势应该仍然存在
        trends = repo.get_recent_trends(hours=24)
        assert len(trends) >= 1

    def test_get_topic_trends_with_limit(self, repo):
        """测试获取话题趋势（带限制）"""
        # 创建多个趋势记录
        for i in range(5):
            repo.create(
                hot_topic_id="topic-012",
                hot_topic_title=f"趋势{i}",
                heat_score=800 + i * 10,
                trend_direction="up"
            )

        # 查询限制数量
        trends = repo.get_topic_trends("topic-012", limit=3)
        assert len(trends) == 3

    def test_trend_direction_variations(self, repo):
        """测试不同趋势方向"""
        # 创建不同方向的记录
        up_trend = repo.create(
            hot_topic_id="topic-013",
            hot_topic_title="上升",
            heat_score=1000,
            trend_direction="up"
        )
        down_trend = repo.create(
            hot_topic_id="topic-014",
            hot_topic_title="下降",
            heat_score=800,
            trend_direction="down"
        )
        stable_trend = repo.create(
            hot_topic_id="topic-015",
            hot_topic_title="平稳",
            heat_score=500,
            trend_direction="stable"
        )

        assert up_trend.trend_direction == "up"
        assert down_trend.trend_direction == "down"
        assert stable_trend.trend_direction == "stable"