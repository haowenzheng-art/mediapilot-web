"""测试数据库表创建"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from backend.models.database.base import Base
from backend.models.database.tables import UserTable, CalendarEventTable, TaskTable

test_engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})

# 创建所有表
Base.metadata.create_all(bind=test_engine, checkfirst=False)

# 检查创建的表
with test_engine.connect() as conn:
    result = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = result.fetchall()
    print(f'Created tables: {[row[0] for row in tables]}')

# 检查表名
print(f'UserTable name: {UserTable.__tablename__}')
print(f'CalendarEventTable name: {CalendarEventTable.__tablename__}')
print(f'TaskTable name: {TaskTable.__tablename__}')
