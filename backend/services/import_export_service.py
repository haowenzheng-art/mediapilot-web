"""
导入导出服务
处理 CSV/Excel 文件的读写操作
"""
import csv
import io
from typing import List, Dict, Any
from fastapi import UploadFile

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class ImportExportService:
    """导入导出服务"""

    def __init__(self):
        """初始化导入导出服务"""
        pass

    def export_to_csv(self, data: List[Dict[str, Any]], filename: str = "export") -> str:
        """
        将数据导出为 CSV

        Args:
            data: 数据列表，每个元素是一个字典
            filename: 文件名（不含扩展名）

        Returns:
            CSV 字符串

        Raises:
            ValueError: 数据为空
        """
        if not data:
            raise ValueError("没有可导出的数据")

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys(), lineterminator='\n')
        writer.writeheader()
        writer.writerows(data)

        return output.getvalue()

    def export_to_excel(self, data: List[Dict[str, Any]], filename: str = "export") -> bytes:
        """
        将数据导出为 Excel

        Args:
            data: 数据列表，每个元素是一个字典
            filename: 文件名（不含扩展名）

        Returns:
            Excel 文件字节

        Raises:
            ValueError: 数据为空或 pandas 未安装
        """
        if not HAS_PANDAS:
            raise ValueError("导出Excel需要安装pandas和openpyxl: pip install pandas openpyxl")

        if not data:
            raise ValueError("没有可导出的数据")

        df = pd.DataFrame(data)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        return output.getvalue()

    def import_from_csv(self, file_content: str) -> List[Dict[str, Any]]:
        """
        从 CSV 导入数据

        Args:
            file_content: CSV 文件内容字符串

        Returns:
            数据字典列表

        Raises:
            ValueError: 解析失败
        """
        if not file_content.strip():
            raise ValueError("文件内容为空")

        input_stream = io.StringIO(file_content)
        reader = csv.DictReader(input_stream)

        data = []
        for row in reader:
            # 移除空值的键
            cleaned_row = {k: v for k, v in row.items() if k}
            data.append(cleaned_row)

        if data:
            return data

        raise ValueError("CSV 文件中没有数据行")

    def import_from_excel(self, file_content: bytes) -> List[Dict[str, Any]]:
        """
        从 Excel 导入数据

        Args:
            file_content: Excel 文件字节

        Returns:
            数据字典列表

        Raises:
            ValueError: 解析失败或 pandas 未安装
        """
        if not HAS_PANDAS:
            raise ValueError("导入Excel需要安装pandas和openpyxl: pip install pandas openpyxl")

        if not file_content:
            raise ValueError("文件内容为空")

        input_stream = io.BytesIO(file_content)
        df = pd.read_excel(input_stream, engine='openpyxl')

        data = df.to_dict('records')
        data = [{k: v for k, v in row.items() if k} for row in data]

        if data:
            return data

        raise ValueError("Excel 文件中没有数据行")

    async def import_from_upload_file(
        self,
        file: UploadFile,
        file_format: str = None
    ) -> List[Dict[str, Any]]:
        """
        从上传的文件导入数据

        Args:
            file: 上传的文件对象
            file_format: 文件格式（csv/xlsx），自动检测

        Returns:
            数据字典列表

        Raises:
            ValueError: 文件格式不支持或解析失败
        """
        # 自动检测文件格式
        if file_format is None:
            filename = file.filename.lower()
            if filename.endswith('.csv'):
                file_format = 'csv'
            elif filename.endswith(('.xls', '.xlsx')):
                file_format = 'xlsx'
            else:
                raise ValueError(f"不支持的文件类型: {file.filename}")

        # 读取文件内容
        content = await file.read()

        if file_format == 'csv':
            content_str = content.decode('utf-8')
            return self.import_from_csv(content_str)
        elif file_format == 'xlsx':
            return self.import_from_excel(content)
        else:
            raise ValueError(f"不支持的文件格式: {file_format}")

    def export_hot_topics(self, topics: List[Any], format_type: str = "csv") -> str | bytes:
        """
        导出热点话题

        Args:
            topics: 热点话题列表
            format_type: 导出格式（csv/xlsx）

        Returns:
            文件内容（字符串或字节）
        """
        data = []
        for topic in topics:
            # 支持字典或对象
            if hasattr(topic, 'model_dump'):
                topic_dict = topic.model_dump()
            elif hasattr(topic, 'dict'):
                topic_dict = topic.dict()
            elif isinstance(topic, dict):
                topic_dict = topic
            else:
                # 尝试转换为字典
                topic_dict = {
                    'keyword': getattr(topic, 'keyword', str(topic)),
                    'platform': getattr(topic, 'platform', ''),
                    'hot_index': getattr(topic, 'hot_index', 0),
                    'trend': getattr(topic, 'trend', '')
                }

            data.append(topic_dict)

        if format_type == 'csv':
            return self.export_to_csv(data, "hot_topics")
        elif format_type == 'xlsx':
            return self.export_to_excel(data, "hot_topics")
        else:
            raise ValueError(f"不支持的导出格式: {format_type}")

    def export_competitors(self, accounts: List[Any], format_type: str = "csv") -> str | bytes:
        """
        导出对标账号

        Args:
            accounts: 对标账号列表（Pydantic 或 dict）
            format_type: 导出格式（csv/xlsx）

        Returns:
            文件内容（字符串或字节）
        """
        data = []
        for acc in accounts:
            if hasattr(acc, 'model_dump'):
                data.append(acc.model_dump())
            elif hasattr(acc, 'dict'):
                data.append(acc.dict())
            elif isinstance(acc, dict):
                data.append(acc)
            else:
                data.append({
                    'account_id': getattr(acc, 'account_id', ''),
                    'nickname': getattr(acc, 'nickname', ''),
                    'platform': getattr(acc, 'platform', ''),
                    'followers': getattr(acc, 'followers', 0),
                    'avg_likes': getattr(acc, 'avg_likes', 0),
                })

        if format_type == 'csv':
            return self.export_to_csv(data, "competitors")
        elif format_type == 'xlsx':
            return self.export_to_excel(data, "competitors")
        else:
            raise ValueError(f"不支持的导出格式: {format_type}")

# 全局导入导出服务实例
import_export_service = ImportExportService()
