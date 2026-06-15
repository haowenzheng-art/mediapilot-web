"""
日历服务单元测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import pytest
from unittest.mock import Mock, MagicMock

from backend.services.calendar_service import CalendarService
from backend.models.domain.calendar import CalendarEventCreate, CalendarEventUpdate, CalendarEventResponse


@pytest.fixture
def calendar_service():
    """日历服务实例"""
    return CalendarService()


@pytest.fixture
def mock_db():
    """Mock 数据库会话"""
    return MagicMock()


@pytest.fixture
def mock_user():
    """Mock 用户"""
    user = Mock()
    user.id = 1
    user.username = "testuser"
    return user


@pytest.fixture
def sample_event_data():
    """示例事件数据"""
    return CalendarEventCreate(
        title="测试发布",
        content="测试内容",
        scheduled_date=datetime.now() + timedelta(days=1),
        platform="douyin",
        status="pending"
    )


def test_create_event_success(calendar_service, mock_db, mock_user, sample_event_data):
    """测试成功创建事件"""
    # Mock database operations - return configured object
    mock_event = Mock()
    mock_event.id = 1
    mock_event.title = sample_event_data.title
    mock_event.content = sample_event_data.content
    mock_event.user_id = mock_user.id

    result = calendar_service.create_event(mock_db, mock_user.id, sample_event_data)

    assert result.title == sample_event_data.title
    assert result.content == sample_event_data.content
    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()


def test_create_event_invalid_status(calendar_service, mock_db, mock_user):
    """测试无效状态值"""
    event_data = CalendarEventCreate(
        title="测试发布",
        scheduled_date=datetime.now() + timedelta(days=1),
        status="invalid_status"
    )

    with pytest.raises(ValueError) as exc_info:
        calendar_service.create_event(mock_db, mock_user.id, event_data)

    assert "状态值无效" in str(exc_info.value)


def test_get_event_success(calendar_service, mock_db, mock_user):
    """测试成功获取事件"""
    # Mock database query
    mock_event = Mock()
    mock_event.id = 1
    mock_event.title = "测试事件"
    mock_event.user_id = mock_user.id
    mock_event.scheduled_date = datetime.now()
    mock_event.content = "测试内容"
    mock_event.platform = "douyin"
    mock_event.status = "pending"
    mock_event.created_at = datetime.now()
    mock_event.updated_at = None

    # Create query mock
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = mock_event

    mock_db.query.return_value = mock_query

    result = calendar_service.get_event(mock_db, mock_user.id, 1)

    assert result is not None


def test_get_events_empty(calendar_service, mock_db, mock_user):
    """测试空事件列表"""
    # Mock empty query result
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.count.return_value = 0
    mock_query.offset.return_value.limit.return_value.all.return_value = []

    mock_db.query.return_value = mock_query

    events, total = calendar_service.get_events(mock_db, mock_user.id)

    assert events == []
    assert total == 0


def test_get_events_with_pagination(calendar_service, mock_db, mock_user):
    """测试分页功能"""
    # Create mock events
    event1 = Mock()
    event1.id = 1
    event1.title = "事件1"
    event1.user_id = mock_user.id
    event1.scheduled_date = datetime.now()
    event1.content = "内容1"
    event1.platform = "douyin"
    event1.status = "pending"
    event1.created_at = datetime.now()
    event1.updated_at = None

    event2 = Mock()
    event2.id = 2
    event2.title = "事件2"
    event2.user_id = mock_user.id
    event2.scheduled_date = datetime.now() + timedelta(days=2)
    event2.content = "内容2"
    event2.platform = "douyin"
    event2.status = "pending"
    event2.created_at = datetime.now()
    event2.updated_at = None

    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.count.return_value = 2
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value.limit.return_value.all.return_value = [event1]

    mock_db.query.return_value = mock_query

    events, total = calendar_service.get_events(
        mock_db, mock_user.id, page=1, per_page=1
    )

    assert len(events) == 1
    assert total == 2


def test_update_event_success(calendar_service, mock_db, mock_user):
    """测试成功更新事件"""
    # Mock existing event
    mock_event = Mock()
    mock_event.id = 1
    mock_event.title = "原标题"
    mock_event.user_id = mock_user.id
    mock_event.content = "原内容"
    mock_event.scheduled_date = datetime.now()
    mock_event.platform = "douyin"
    mock_event.status = "pending"
    mock_event.created_at = datetime.now()
    mock_event.updated_at = None

    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_event
    mock_db.query.return_value = mock_query

    update_data = CalendarEventUpdate(title="更新后的标题")

    result = calendar_service.update_event(mock_db, mock_user.id, 1, update_data)

    assert result.title == "更新后的标题"


def test_update_event_not_found(calendar_service, mock_db, mock_user):
    """测试更新不存在的事件"""
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = None
    mock_db.query.return_value = mock_query

    update_data = CalendarEventUpdate(title="新标题")

    result = calendar_service.update_event(mock_db, mock_user.id, 999, update_data)

    assert result is None


def test_delete_event_success(calendar_service, mock_db, mock_user):
    """测试成功删除事件"""
    mock_event = Mock()
    mock_event.id = 1
    mock_event.user_id = mock_user.id

    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_event
    mock_db.query.return_value = mock_query

    mock_db.query.return_value = mock_query
    mock_db.delete.return_value = mock_db

    result = calendar_service.delete_event(mock_db, mock_user.id, 1)

    assert result is True
    mock_db.delete.assert_called_once()


def test_delete_event_not_found(calendar_service, mock_db, mock_user):
    """测试删除不存在的事件"""
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = None
    mock_db.query.return_value = mock_query

    result = calendar_service.delete_event(mock_db, mock_user.id, 999)

    assert result is False


def test_get_upcoming_events(calendar_service, mock_db, mock_user):
    """测试获取即将到来事件"""
    event1 = Mock()
    event1.id = 1
    event1.title = "事件1"
    event1.user_id = mock_user.id
    event1.scheduled_date = datetime.now() + timedelta(days=1)
    event1.status = "pending"
    event1.content = "内容1"
    event1.platform = "douyin"
    event1.created_at = datetime.now()
    event1.updated_at = None

    event2 = Mock()
    event2.id = 2
    event2.title = "事件2"
    event2.user_id = mock_user.id
    event2.scheduled_date = datetime.now() + timedelta(days=3)
    event2.status = "pending"
    event2.content = "内容2"
    event2.platform = "douyin"
    event2.created_at = datetime.now()
    event2.updated_at = None

    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = [event1, event2]
    mock_db.query.return_value = mock_query

    result = calendar_service.get_upcoming_events(mock_db, mock_user.id, 7)

    assert len(result) == 2
    for event in result:
        assert event.status == "pending"
