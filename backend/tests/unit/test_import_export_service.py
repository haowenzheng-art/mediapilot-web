"""
导入导出服务单元测试
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO

from backend.services.import_export_service import ImportExportService


@pytest.fixture
def import_export_service():
    """导入导出服务实例"""
    return ImportExportService()


def test_export_to_csv_success(import_export_service):
    """测试成功导出 CSV"""
    data = [
        {"name": "张三", "age": 25, "city": "北京"},
        {"name": "李四", "age": 30, "city": "上海"}
    ]

    result = import_export_service.export_to_csv(data, "users")

    assert "name,age,city" in result
    assert "张三,25,北京" in result
    assert "李四,30,上海" in result


def test_export_to_csv_empty(import_export_service):
    """测试导出空数据"""
    with pytest.raises(ValueError) as exc_info:
        import_export_service.export_to_csv([], "test")

    assert "没有可导出的数据" in str(exc_info.value)


def test_import_from_csv_success(import_export_service):
    """测试成功导入 CSV"""
    csv_content = """name,age,city
张三,25,北京
李四,30,上海
"""

    result = import_export_service.import_from_csv(csv_content)

    assert len(result) == 2
    assert result[0]["name"] == "张三"
    assert result[0]["age"] == "25"
    assert result[1]["name"] == "李四"


def test_import_from_csv_empty(import_export_service):
    """测试导入空 CSV"""
    with pytest.raises(ValueError):
        import_export_service.import_from_csv("")


def test_import_from_csv_invalid(import_export_service):
    """测试导入无效 CSV"""
    with pytest.raises(ValueError):
        import_export_service.import_from_csv("name\n")  # 只有表头，没有数据


@pytest.mark.skipif(
    not ImportExportService.__dict__.get('HAS_PANDAS', False),
    reason="pandas not installed"
)
def test_export_to_excel_success(import_export_service):
    """测试成功导出 Excel（需要 pandas）"""
    data = [
        {"name": "张三", "age": 25, "city": "北京"},
        {"name": "李四", "age": 30, "city": "上海"}
    ]

    result = import_export_service.export_to_excel(data, "users")

    assert isinstance(result, bytes)
    assert len(result) > 0


@pytest.mark.skipif(
    not ImportExportService.__dict__.get('HAS_PANDAS', False),
    reason="pandas not installed"
)
def test_export_to_excel_empty(import_export_service):
    """测试导出空 Excel"""
    with pytest.raises(ValueError) as exc_info:
        import_export_service.export_to_excel([], "test")

    assert "没有可导出的数据" in str(exc_info.value)


@pytest.mark.skipif(
    not ImportExportService.__dict__.get('HAS_PANDAS', False),
    reason="pandas not installed"
)
def test_import_from_excel_success(import_export_service):
    """测试成功导入 Excel（需要 pandas）"""
    # 创建模拟的 Excel 内容
    import pandas as pd
    df = pd.DataFrame([
        {"name": "张三", "age": 25},
        {"name": "李四", "age": 30}
    ])

    excel_bytes = BytesIO()
    df.to_excel(excel_bytes, index=False, engine='openpyxl')
    excel_bytes.seek(0)

    result = import_export_service.import_from_excel(excel_bytes.getvalue())

    assert len(result) == 2
    assert result[0]["name"] == "张三"


def test_export_hot_topics_with_dict(import_export_service):
    """测试导出热点话题（字典格式）"""
    topics = [
        {"keyword": "AI", "platform": "douyin", "hot_index": 1000, "trend": "up"},
        {"keyword": "编程", "platform": "weibo", "hot_index": 800, "trend": "stable"}
    ]

    result = import_export_service.export_hot_topics(topics, "csv")

    assert "keyword,platform,hot_index,trend" in result
    assert "AI,douyin,1000,up" in result


def test_export_hot_topics_with_object(import_export_service):
    """测试导出热点话题（对象格式）"""
    class MockTopic:
        def __init__(self, keyword, platform, hot_index):
            self.keyword = keyword
            self.platform = platform
            self.hot_index = hot_index

    topics = [MockTopic("AI", "douyin", 1000)]

    result = import_export_service.export_hot_topics(topics, "csv")

    assert "AI,douyin,1000" in result


def test_export_competitors_with_dict(import_export_service):
    """测试导出对标账号（字典格式）"""
    accounts = [
        {"username": "user1", "platform": "douyin", "niche": "科技", "followers": 10000},
        {"username": "user2", "platform": "xiaohongshu", "niche": "美妆", "followers": 5000}
    ]

    result = import_export_service.export_competitors(accounts, "csv")

    # 检查表头和数据行
    assert "username" in result
    assert "platform" in result
    assert "niche" in result
    assert "followers" in result
    assert "user1" in result
    assert "douyin" in result
    assert "科技" in result
    assert "10000" in result


def test_export_competitors_with_object(import_export_service):
    """测试导出对标账号（对象格式）"""
    class MockAccount:
        def __init__(self, username, platform, followers):
            self.username = username
            self.platform = platform
            self.followers = followers

    accounts = [MockAccount("user1", "douyin", 10000)]

    result = import_export_service.export_competitors(accounts, "csv")

    # 检查基本列名和数据
    assert "username" in result
    assert "platform" in result
    assert "followers" in result
    assert "user1" in result
    assert "douyin" in result
    assert "10000" in result


@pytest.mark.asyncio
async def test_import_from_upload_file_csv(import_export_service):
    """测试从上传的文件导入 CSV"""
    # Mock 文件对象 - read 需要是 async
    mock_file = Mock()
    mock_file.filename = "test.csv"
    mock_file.read = AsyncMock(return_value="name,age\n张三,25\n".encode('utf-8'))

    result = await import_export_service.import_from_upload_file(mock_file, "csv")

    assert len(result) == 1
    assert result[0]["name"] == "张三"


@pytest.mark.asyncio
async def test_import_from_upload_file_auto_detect_csv(import_export_service):
    """测试自动检测 CSV 格式"""
    mock_file = Mock()
    mock_file.filename = "data.csv"
    mock_file.read = AsyncMock(return_value="name\n张三\n".encode('utf-8'))

    result = await import_export_service.import_from_upload_file(mock_file)

    assert len(result) == 1


@pytest.mark.asyncio
async def test_import_from_upload_file_unsupported_format(import_export_service):
    """测试不支持的文件格式"""
    mock_file = Mock()
    mock_file.filename = "data.txt"
    mock_file.read = AsyncMock(return_value="name\n张三\n".encode('utf-8'))

    with pytest.raises(ValueError) as exc_info:
        await import_export_service.import_from_upload_file(mock_file)

    assert "不支持的文件类型" in str(exc_info.value)
