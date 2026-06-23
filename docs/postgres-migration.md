# PostgreSQL 迁移与 Alembic 运维手册

## 目标

把开发用的 SQLite 切换到生产 PostgreSQL，保留可重复迁移能力。

## 0. 一次性准备

### 安装驱动

```bash
pip install psycopg2-binary
```

已加入 `backend/requirements.txt`，新环境 `pip install -r backend/requirements.txt` 即可。

### 创建数据库

```bash
psql -U postgres
CREATE DATABASE mediapilot;
CREATE USER mediapilot WITH PASSWORD 'CHANGE_ME';
GRANT ALL PRIVILEGES ON DATABASE mediapilot TO mediapilot;
```

### 配置环境变量

`.env` 中改 DATABASE_URL：

```bash
DATABASE_URL=postgresql://mediapilot:CHANGE_ME@localhost:5432/mediapilot
```

## 1. 首次部署（空库）

```bash
cd backend
alembic upgrade head
```

会从最早的 `95e4b7d794d8_initial_migration` 一路 upgrade 到当前 `12cf096c1734_sync_models_v1`。

## 2. 从 SQLite 迁数据

如果生产已经在跑 SQLite，要带数据切到 PG：

```bash
# 1. 备份 SQLite
cp mediapilot.db mediapilot.db.bak.$(date +%Y%m%d)

# 2. 在 PG 建表（执行所有迁移）
DATABASE_URL=postgresql://... alembic upgrade head

# 3. 用 pgloader 迁移数据
pgloader sqlite:///path/to/mediapilot.db postgresql://mediapilot:PASS@localhost/mediapilot

# 4. 验证行数
psql -U mediapilot -d mediapilot -c "SELECT count(*) FROM users;"
```

## 3. 日常开发：改了模型怎么办

```bash
# 1. 改 backend/models/database/tables.py，加字段/索引/表
# 2. 生成迁移
cd backend
alembic revision --autogenerate -m "add_xxx_column"
# 3. 审查 alembic/versions/<new>_add_xxx.py（autogenerate 可能漏掉 server_default 之类）
# 4. 应用
alembic upgrade head
```

## 4. 回滚

```bash
# 回退一版
alembic downgrade -1
# 回退到指定 revision
alembic downgrade 3a016db24d47
```

注意：drop column / drop table 通常不可逆，回滚脚本要谨慎编写。

## 5. 当前迁移链

| Revision | Description | 时间 |
|----------|-------------|------|
| 95e4b7d794d8 | initial_migration | baseline (users, hot_topics) |
| 3a016db24d47 | add_copywriting_table | copywritings + persona |
| 12cf096c1734 | sync_models_v1 | subscriptions / push_records / tasks / token_blacklist / content_library / shoot_scripts / hot_topic_trends 等所有当前表 |

## 6. 故障排查

| 症状 | 原因 | 处理 |
|------|------|------|
| `relation "x" already exists` 在 upgrade 时 | DB 已有表但 alembic 不知道 | `alembic stamp head` 标记当前版本，再开发新迁移 |
| `Can't locate revision identified by 'xxx'` | versions 目录缺文件 | 同步 versions/ 到对应 git 版本 |
| autogenerate 没检测到改动 | 模型没被 import 进 Base.metadata | 检查 `backend/models/database/__init__.py` 导入链 |

## 7. 生产部署 checklist

- [ ] DATABASE_URL 指向 PG（不是 sqlite）
- [ ] JWT_SECRET 是 32+ 字符随机串
- [ ] DEV_MODE=false
- [ ] `alembic current` 显示最新 head
- [ ] PG 备份计划（`pg_dump` 每日定时）
- [ ] Redis 启动（ARQ worker 依赖）
