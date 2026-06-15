# MediaPilot 数据库架构审查

## 当前状态

### 现有表结构

```python
# backend/models/database/tables.py

class TaskTable(Base):
    __tablename__ = "tasks"
    task_id = Column(String(36), primary_key=True, index=True)
    status = Column(String(20), nullable=False, default="pending")
    transcript = Column(Text, nullable=True)
    outline = Column(JSONColumn, nullable=True)
    timestamps = Column(JSONColumn, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class UserTable(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    quota_balance = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)
    is_admin = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class CalendarEventTable(Base):
    __tablename__ = "calendar_events"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=True)
    scheduled_date = Column(DateTime, nullable=False, index=True)
    platform = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

---

## 审查结果

### ✅ 良好的方面

1. **表设计合理**
   - 任务表支持工作流（status, transcript, outline, timestamps）
   - 用户表有完整的认证和配额管理
   - 日历事件表支持多平台

2. **索引配置合理**
   - 所有主键都有 index=True
   - username 和 email 有 unique=True 防止重复

3. **时间戳完整**
   - 每个表都有 created_at 和 updated_at
   - 使用 server_default=func.now() 和 onupdate=func.now()

4. **JSON 处理正确**
   - 使用自定义 JSONColumn 处理复杂 JSON 数据
   - 支持 SQLite 数据库

5. **数据类型合理**
   - Integer 用于 ID 和配额
   - String 用于用户名、邮箱等
   - Boolean 用于激活状态
   - Text 用于长文本
   - DateTime 用于时间戳

---

## ⚠️ 建议改进

### 1. 索引优化

```python
# 添加复合索引以提高查询性能

class UserTable(Base):
    __tablename__ = "users"
    # ... 现有字段 ...
    
    # 添加复合索引
    __table_args__ = (
        Index('idx_username_email', 'username', 'email'),  # 用户名和邮箱联合查询
        Index('idx_active_quota', 'is_active', 'quota_balance'),  # 活跃用户按配额查询
    )
```

### 2. 添加软删除字段

```python
class TaskTable(Base):
    __tablename__ = "tasks"
    # ... 现有字段 ...
    
    # 添加软删除标记
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # 修改查询以过滤软删除的记录
    # __mapper_args__ = {"polymorphic_identity": True}
```

### 3. 添加任务关联

```python
# 如果需要跟踪任务之间的关系
class TaskRelation(Base):
    __tablename__ = "task_relations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_task_id = Column(String(36), nullable=True, index=True)
    child_task_id = Column(String(36), nullable=True, index=True)
    relation_type = Column(String(20), nullable=False)  # "dependency", "duplicate"
    created_at = Column(DateTime, server_default=func.now())
```

### 4. 添加缓存/性能优化表

```python
# 添加查询结果缓存
class QueryCache(Base):
    __tablename__ = "query_cache"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(255), nullable=False, index=True, unique=True)
    cache_value = Column(Text, nullable=True)
    cache_ttl = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)
```

### 5. 数据库连接池优化

```python
# 在 config/database.py 中添加连接池配置

from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # 最大连接数
    max_overflow=20,  # 允许的最大溢出连接数
    pool_timeout=30,  # 连接超时时间（秒）
    pool_recycle=3600,  # 连接回收时间（秒）
)
```

---

## 📊 实现优先级

| 优先级 | 说明 |
|--------|------|
| **P0** | 基础表结构优化（索引、复合索引） |
| **P1** | 软删除功能（避免数据丢失） |
| **P2** | 任务关联和流程跟踪 |
| **P3** | 缓存系统（减少重复查询） |
| **P4** | 连接池优化（性能提升） |

---

## ✅ 总结

当前数据库架构**基本合理**，主要改进方向：

1. **立即实施**：添加复合索引（username + email）
2. **短期实施**：添加软删除支持，避免直接删除数据
3. **中期实施**：添加任务关联表，支持复杂工作流
4. **长期实施**：实现查询缓存和连接池优化

需要我继续执行后续任务吗？
