# MediaPilot 代码规范与项目文档

---

## 目录

1. [项目简介](#项目简介)
2. [代码规范](#代码规范)
3. [部署指南](#部署指南)
4. [项目进度](#项目进度)

---

## 项目简介

**MediaPilot - 媒体领航员**

为新媒体行业打造的全功能AI助手App，助力内容创作者高效工作！

### 功能特性

- 🔥 **热点追踪** - 按指令搜索行业最近一周热点
- 🎯 **对标分析** - 在小红书、抖音找到赛道对标账号，支持Excel导出
- 🎬 **爆款分析** - 自动分析爆款视频，生成逐字稿和改写文案
- 🎤 **音视频转写** - 支持mp3/mp4文件，一键语音转文字并生成大纲
- ✍️ **内容生成** - 对特定选题生成分镜头脚本和文案建议
- 📊 **数据看板** - 账号数据趋势分析
- 📅 **内容日历** - 规划发布排期
- 🤖 **AI助手** - 多模型支持（Claude/GPT/火山方舟）

### 技术栈

- **后端**: FastAPI + Python
- **Windows端**: PyQt5
- **移动端**: Flutter
- **数据库**: SQLite
- **AI集成**: Claude / GPT / 火山方舟

### 项目结构

```
MediaPilot/
├── backend/          # 后端API服务
├── desktop/          # Windows桌面端
├── mobile/           # 移动端
├── shared/           # 共享配置和工具
└── docs/             # 文档
```

---

## 代码规范

### 一、模块拆分原则（职责单一）

#### 1.1 职责单一原则 (SRP)

每个模块只负责一个明确的功能领域：

- **api/**: 仅处理 HTTP 请求/响应，不包含业务逻辑
- **services/**: 核心业务逻辑，可被多个入口调用
- **repository/**: 数据库 CRUD 操作，不包含业务规则
- **models/**: 数据结构定义，无逻辑处理
- **core/**: 外部系统交互（AI、第三方API等）
- **utils/**: 纯工具函数，无状态，可测试

#### 1.2 依赖方向

```
api → services → repository → models
        ↓
     core
```

禁止反向依赖：
- ❌ service 不能调用 api
- ❌ repository 不能调用 service
- ❌ model 不能调用任何业务层

#### 1.3 层级边界

| 层级 | 能做的事情 | 不能做的事情 |
|------|------|---------|
| API | 参数校验、调用 Service、格式化响应 | 直接操作数据库、包含业务逻辑 |
| Service | 组合业务逻辑、调用 Repository、调用 Core Service | 处理 HTTP、直接访问数据库 |
| Repository | 数据库 CRUD 操作 | 业务判断、格式化数据 |
| Model | | 任何逻辑处理 |

---

### 二、命名规范

#### 2.1 文件命名

##### Python (后端)

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写，下划线分隔 | `trending_service.py` |
| 类模块 | 小写，下划线分隔 | `hot_topic.py` |
| 测试文件 | `test_` + 模块名 | `test_trending_service.py` |

#####的后端推荐下划线：`trending_service/`
- 前端推荐连字符：`use-theme/`

---

### 三、模块间引用规范

#### 3.1 入口文件暴露原则

每个目录必须有 `__init__.py` / `index.js`，统一暴露接口：

```python
# services/__init__.py
from .trending_service import TrendingService
from .competitor_service import CompetitorService

__all__ = ['TrendingService', 'CompetitorService']
```

```javascript
// components/index.jsx
export { default as Button } from './Button'
export { default as Modal } from './Modal'
```

#### 3.2 引用规范

```python
# 推荐：通过入口文件引用
from services import TrendingService

# 避免：直接引用内部模块
from services.trending_service import TrendingService
```

#### 3.3 循环引用检测

如果出现循环引用：
1. 检查是否违反依赖方向原则
2. 将共享部分抽取到独立模块
3. 使用依赖注入解耦

---

### 四、代码风格与注释要求

#### 4.1 Python 遵循 PEP 8

使用 `black` 格式化：
```bash
pip install black
black backend/
```

#### 4.2 JavaScript 使用 ESLint + Prettier

```json
{
  "extends": ["eslint:recommended", "prettier"],
  "rules": {
    "semi": ["error", "always"],
    "quotes": ["single"]
  }
}
```

#### 4.3 注释规范

##### 文件头部部注释

```python
"""
MediaPilot 热点搜索服务

职责：
- 处理热点搜索业务逻辑

作者：xxx
创建时间：2026-03-25
"""
```

```javascript
/**
 * 热点搜索页面
 *
 * 功能：
 * - 输入关键词搜索热点
 * - 显示各平台热度趋势
 * - 支持导出结果
 */
```

##### 函数注释

```python
def search_trending(keyword: str, platforms: list, days: int) -> List[HotTopic]:
    """
    搜索热点话题

    Args:
        keyword: 搜索关键词
        platforms: 平台列表
        days: 搜索天数，范围 1-30

    Returns:
        热点话题列表，按热度降序

    Raises:
        ValueError: 关键词不合法
    """
    pass
```

```javascript
/**
 * 搜索热点话题
 * @param {string} keyword - 搜索关键词
 * @param {string[]} platforms - 平台列表
 * @param {number} days - 搜索天数
 * @returns {Promise<HotTopic[]>} 热点话题列表
 */
async function searchTrending(keyword, platforms, days) {}
```

#### 4.4 禁止事项

- ❌ 禁止无意义的注释（如 `i += 1  # 加1`）
- ❌ 禁止注释掉的代码（使用 Git 管理）
- ❌ 禁止行内注释影响代码可读性
- ❌ 禁止魔法数字，使用常量替代

---

### 五、Git 提交规范

使用 Conventional Commits 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type 类型

| 类型 | 说明 |
|------|------|
| feat | 新功能 |
| fix | 修复bug |
| refactor | 重构代码 |
| docs | 文档变更 |
| style | 代码格式调整 |
| test | 测试相关 |
| chore | 构建/工具相关 |

#### 示例

```bash
git commit -m "feat(services): 添加热点搜索业务逻辑

- 从 mock_data 提取搜索逻辑
- 封装到 TrendingService 类
- 提取入参数校验

Closes #123"
```

---

### 六、测试规范

#### 6.1 测试文件结构

```
backend/
├── tests/
│   ├── unit/
│   │   └── test_trending_service.py
│   └── integration/
│   │   └── test_api_trending.py
```

#### 6.2 测试命名

```
def test_功能_场景_预期():
    pass
```

#### 6.3 测试覆盖

- 核心 Service 层单元测试覆盖率 > 80%
- API 层集成测试覆盖所有端点
- 边界组件测试关键用户路径

---

### 七、配置管理

#### 7.1 环境变量

使用 `.env` 文件，不提交到 Git：

```bash
# .env
API_KEY=sk-xxx
DATABASE_URL=sqlite:///./mediapilot.db
AI_MODEL=claude-3-opus-20240229
```

#### 7.2 敏感信息

绝对禁止：
- ❌ 代码中硬编码 API Key
- ❌ 提交 `.env` 文件
- ❌ 日志输出敏感（密码、token、个人信息）

#### 7.3 配置类

- 使用 `pydantic-settings` 管理配置：
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_key: str = Field(default="", description="API Key")
    database_url: str = Field(default="sqlite:///./mediapilot.db")
```

---

### 八、持续检查

在 CI/CD 中运行：

```bash
# 后端
black --check backend/
pylint backend/
pytest backend/tests/

# 前端
eslint web/src/
prettier --check web/src/
```

---

### 九、架构演进最佳实践（从 Phase 1-3 重构总结）

#### 9.1 三层架构模式

**API 层（路由）**
- 仅负责参数校验、调用 Service、格式化响应
- 每个业务领域独立路由文件：`trending.py`, `competitors.py`, `content.py` 等
- 使用 `APIRouter(prefix="/xxx")` 统一前缀
- 使用 `register_routes(app)` 集中注册所有路由

**Service 层（业务逻辑）**
- 核心业务逻辑封装在 `XXXService` 类中
- 可被多个入口调用（API、命令行、测试）
- 不处理 HTTP 相关逻辑

**Repository 层（数据访问）**
- 使用 SQLAlchemy ORM 进行数据库操作
- 提供 `BaseRepository` 泛型基类封装通用 CRUD
- 具体仓库继承基类实现特定业务查询

#### 9.2 模块间引用规范

**路径管理**
- 在模块文件顶部统一管理 Python 路径：
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```
- 注意括号匹配：3个 `os.path.dirname()` 需要 3个右括号

**导入优先级**
1. 优先使用新路径结构：`from backend.services import xxx`
2. 保留旧路径兼容：`except ImportError: from shared import xxx`

#### 9.3 路由模块化

**单个路由文件模板**
```python
"""
功能描述路由
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter
from models.schemas.request import XXXRequest
from models.schemas.response import APIResponse
from services.xxx_service import XXXService

router = APIRouter(prefix="/xxx", tags=["功能名称"])

# 初始化服务
xxx_service = XXXService()

@router.post("/endpoint", response_model=APIResponse)
async def handler(request: XXXRequest):
    """处理请求"""
    result = await xxx_service.method(...)
    return APIResponse(data=result)
```

#### 9.4 环境变量配置

- 使用 `pydantic-settings` 管理配置
- 配置类统一放在 `backend/config/settings.py`
- 通过 `from config.settings import settings` 导入
- 环境变量读取：`os.getenv("KEY", default_value)`

#### 9.5 迁移兼容策略

从单体结构迁移到分层结构时：
1. 先创建新结构文件
2. 保留旧文件作为 fallback
3. 使用 try-except 导入保证向后兼容
4. 验证新结构工作后再删除旧文件

---

## 部署指南

### 一、环境要求

| 依赖 | 版本要求 | 说明 |
|------|----------|------|
| Docker | >= 20.10 | 容器运行时 |
| Docker Compose | >= 2.0 | 容器编排 |
| Nginx | >= 1.18 | 反向代理（可选） |
| 域名 | - | HTTPS 证书需要 |

---

### 二、快速部署（本地/测试）

#### 2.1 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入实际配置
# 必须修改：JWT_SECRET（生产环境）
```

#### 2.2 启动服务

```bash
# 构建并启动（后台运行）
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 停止并删除数据卷（慎用）
docker-compose down -v
```

#### 2.3 验证服务

```bash
# 健康检查
curl http://localhost:8000/health
# 预期返回：{"status":"healthy"}

# 前端访问
curl http://localhost:80/health
# 预期返回：healthy

# API 根路径
curl http://localhost:8000/
# 预期返回：{"name":"MediaPilot API","version":"1.0.0","status":"running"}
```

---

### 三、生产环境部署

#### 3.1 准备域名和证书

使用 Let's Encrypt 获取免费 SSL 证书：

```bash
# 安装 certbot
apt-get update && apt-get install -y certbot

# 获取证书（替换 your-domain.com）
certbot certonly --standalone -d your-domain.com

# 证书路径
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

#### 3.2 配置 Nginx 反向代理

创建 Nginx 配置文件 `/etc/nginx/sites-available/mediapilot`：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;

    # 前端静态文件
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 健康检查
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
```

启用配置：

```bash
ln -s /etc/nginx/sites-available/mediapilot /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

#### 3.3 修改 docker-compose.yml 端口映射

修改 `docker-compose.yml`，将内部端口映射到 localhost：

```yaml
services:
  backend:
    ports:
      - "127.0.0.1:8000:8000"  # 仅本机可访问

  frontend:
    ports:
      - "127.0.0.1:3000:80"    # 仅本机可访问
```

#### 3.4 配置生产环境变量

编辑 `.env` 文件，生产环境必须修改以下配置：

```bash
# 必须修改（强密钥）
JWT_SECRET=<生成一个强随机字符串>

# 生产环境建议使用 PostgreSQL 或 MySQL
DATABASE_URL=postgresql://user:password@localhost:5432/mediapilot

# 设置 CORS 允许的源
CORS_ORIGINS=https://your-domain.com

# 日志级别建议使用 INFO 或 WARNING
LOG_LEVEL=INFO
```

生成强密钥：

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### 四、数据库初始化

#### 4.1 SQLite（默认）

自动初始化，无需手动操作。数据库文件存储在 Docker 卷 `backend_db` 中。

#### 4.2 PostgreSQL / MySQL

##### 安装数据库服务

```bash
# PostgreSQL
apt-get install -y postgresql postgresql-contrib

# MySQL
apt-get install -y mysql-server
```

##### 创建数据库和用户

```sql
-- PostgreSQL
CREATE USER mediapilot WITH PASSWORD 'your_password';
CREATE DATABASE mediapilot OWNER mediapilot;

-- MySQL
CREATE USER 'mediapilot'@'localhost' IDENTIFIED BY 'your_password';
CREATE DATABASE mediapilot;
GRANT ALL PRIVILEGES ON mediapilot.* TO 'mediapilot'@'localhost';
```

##### 数据库迁移

项目使用 SQLAlchemy 自动建表，无需手动迁移。

如需重置数据库：

```bash
# 删除数据卷
docker-compose down -v

# 重新启动（自动建表）
docker-compose up -d
```

---

### 五、验证部署

#### 5.1 健康检查

```bash
# 后端健康检查
curl https://your-domain.com/health

# 前端访问
curl https://your-domain.com

# API 访问
curl https://your-domain.com/api/
```

#### 5.2 功能测试

创建测试用户：

```bash
# 注册用户
curl -X POST https://your-domain.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "StrongPassword123",
    "email": "admin@example.com"
  }'

# 保存返回的 token

# 获取用户信息
TOKEN=<your_token>
curl https://your-domain.com/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

#### 5.3 检查日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend
```

---

### 六、监控和日志

#### 6.1 日志收集

Docker 日志位置：

```bash
# 查看容器日志
docker logs mediapilot-backend
docker logs mediapilot-frontend
```

应用日志（如果配置了文件日志）：

```bash
# 后端日志
docker exec mediapilot-backend cat /app/server.log

# Nginx 日志（如果使用外部 Nginx）
tail -f /var/log/nginx/mediapilot_access.log
tail -f /var/log/nginx/mediapilot_error.log
```

#### 6.2 监控建议

- **资源监控**：使用 Docker stats
  ```bash
  docker stats
  ```

- **健康检查**：定期调用 `/health` 端点

- **日志监控推荐**：
  - ELK Stack（Elasticsearch + Logstash + Kibana）
  - Loki + Grafana
  - 云服务：CloudWatch、阿里云日志服务

---

### 七、故障排查

#### 7.1 服务无法启动

```bash
# 查看容器状态
docker-compose ps

# 查看启动日志
docker-compose logs

# 重新构建
docker-compose up -d --build
```

#### 7.2 数据库连接失败

检查环境变量：

```bash
docker-compose exec backend env | grep DATABASE_URL
```

检查数据库服务是否运行：

```bash
# PostgreSQL
systemctl status postgresql

# MySQL
systemctl status mysql
```

#### 7.3 前端无法访问后端

检查 CORS 配置：

```bash
docker-compose exec backend env | grep CORS_ORIGINS
```

检查 Nginx 配置：

```bash
nginx -t
systemctl status nginx reload
```

#### 7.4 AI 功能不可用

检查 AI 配置：

```bash
docker-compose exec backend env | grep AI_
```

查看启动日志中的 AI 服务状态：

```bash
docker-compose logs backend | grep AI
```

---

### 八、更新部署

#### 8.1 拉取最新代码

```bash
git pull origin main
```

#### 8.2 重新构建和部署

```bash
docker-compose up -d --build
```

#### 8.3 数据库迁移（如有变更）

```bash
# 如果使用了 Alembic
docker-compose exec backend alembic upgrade head
```

---

### 九、备份和恢复

#### 9.1 备份数据库

```bash
# 备份 SQLite
docker cp mediapilot-backend:/app/mediapilot.db ./backup_$(date +%Y%m%d).db

# 备份 PostgreSQL
docker exec postgres pg_dump -U mediapilot mediapilot > backup_$(date +%Y%m%d).sql

# 备份 MySQL
docker exec mysql mysqldump -u mediapilot -p mediapilot > backup_$(date +%Y%m%d).sql
```

#### 9.2 恢复数据库

```bash
# 恢复 SQLite
docker cp backup_20260327.db mediapilot-backend:/app/mediapilot.db
docker-compose restart backend

# 恢复 PostgreSQL
docker exec -i postgres psql -U mediapilot mediapilot < backup_20260327.sql

# 恢复 MySQL
docker exec -i mysql mysql -u mediapilot -p mediapilot < backup_20260327.sql
```

---

### 十、安全建议

1. **修改默认密钥**：生产环境必须修改 `JWT_SECRET`
2. **使用强密码**：数据库、API 密钥等使用强密码
3. **启用 HTTPS**：生产环境必须使用 SSL/TLS
4. **限制访问**：后端端口仅绑定到 127.0.0.1
5. **定期更新**：保持系统和依赖包最新
6. **监控日志**：定期检查访问日志和错误日志
7. **备份策略**：定期备份数据库

---

### 十一、附录

#### 11.1 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重新构建
docker-compose build

# 清理未使用的资源
docker system prune -a
```

#### 11.2 端口说明

| 服务 | 内部端口 | 外部端口（默认） | 说明 |
|------|----------|------------------|------|
| backend | 8000 | 8000 | FastAPI 服务 |
| frontend | 80 | 80 | Nginx 前端服务 |

#### 11.3 环境变量参考

详见 `.env.example` 文件。

#### 11.4 技术支持

如遇问题，请检查：
1. Docker 和 Docker Compose 版本
2. 系统资源（磁盘、内存）
3. 网络连接
4. 环境变量配置正确性

---

## 项目进度

### 已完成阶段

#### Phase 1-5: 后端重构 ✅
- ✅ Phase 1: 后端基础架构（models, repository, services, config, utils）
- ✅ Phase 2: 业务逻辑抽取（services 已填充）
- ✅ Phase 3: 路由拆分（api 目录已拆分）
- ✅ Phase 4: 数据层实现（SQLAlchemy + 任务持久化）

#### Phase 5: 前端重构 ✅
- ✅ 拆分 App.jsx（453 → 234 行）
- ✅ 创建路由配置（routes/）
- ✅ 抽取布局组件（components/layout/）
- ✅ 创建 Hero Section 页面
- ✅ API 改为调用后端

#### Phase 7: 集成测试 ✅
- ✅ 后端单元测试（11/11 通过）
- ✅ 后端集成测试（6/6 通过）
- ✅ 前端测试（5/5 通过）
- ✅ 测试运行环境配置（pytest + Vitest）

### 测试文件
```
backend/
├── pyproject.toml
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_trending_service.py (5个测试)
│   │   └── test_content_service.py (6个测试)
│   └── integration/
│       └── test_api_trending.py (6个测试)
└── run_tests.sh

web/
├── vitest.config.ts
├── vitest.setup.js
└── src/services/api.test.js (5个测试)
```

### 测试运行命令
```bash
# 后端
cd backend
pytest tests/ -v

# 前端
cd web
npm test
```

### 测试结果（Phase 7）
| 类型 | 测试数 | 通过 | 状态 |
|------|--------|------|------|
| 后端单元 | 11 | 11 | ✅ |
| 后端集成 | 6 | 6 | ✅ |
| 前端 | 5 | 5 | ✅ |
| **合计** | **22** | **22** | **✅** |

---

#### Phase 6: 环境配置与部署 ✅
- ✅ 生产环境变量配置（.env.example）
- ✅ 后端 Dockerfile（多阶段构建）
- ✅ 前端 Dockerfile + nginx.conf
- ✅ docker-compose.yml（前后端编排）
- ✅ GitHub Actions CI/CD 配置
- ✅ .dockerignore 文件

### 部署文件
```
MediaPilot/
├── .env.example           # 环境变量示例
├── .dockerignore           # Docker 构建排除文件
├── docker-compose.yml       # 容器编排配置
├── backend/
│   ├── Dockerfile          # 后端容器
│   └── requirements.txt    # 依赖清单
├── web/
│   ├── Dockerfile          # 前端容器
│   └── nginx.conf          # Nginx 配置
└── .github/
    └── workflows/
        └── ci.yml          # CI/CD 流程
```

### 快速部署命令
```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 填入实际值

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

### CI/CD 功能
- ✅ 代码质量检查（black、pylint、ESLint）
- ✅ 后端单元测试 + 覆盖率
- ✅ 前端测试 + 构建
- ✅ Docker 镜像构建
- ✅ 自动部署到生产环境（需配置 SSH 密钥）

---

#### Phase 8: 接入真实 AI 模型 ✅
- ✅ 更新 .env.example 添加 AI 配置项
- ✅ 更新 settings.py 添加 AI 配置类
- ✅ 增强 ai_service.py（超时、重试、错误处理）
- ✅ 更新 main.py 启动时初始化 AI 服务
- ✅ 创建 AI 服务单元测试（test_ai_service.py, 10 个测试）
- ✅ 创建内容 API 集成测试（test_api_content.py, 6 个测试）
- ✅ 更新 content.py 路由使用新 AI 服务

### 新增文件
```
backend/
├── core/ai_service.py        # 增强：超时、重试、错误处理
├── tests/unit/
│   └── test_ai_service.py    # AI 服务单元测试
└── tests/integration/
    └── test_api_content.py    # 内容 API 集成测试
```

### 环境变量配置
```bash
# AI提供商: anthropic, openai, ark
AI_PROVIDER=ark
AI_API_KEY=your_api_key_here
AI_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
AI_MODEL=deepseek-v3-0324
AI_TIMEOUT=60
AI_MAX_RETRIES=3
```

### 测试结果（Phase 8）
| 类型 | 测试数 | 通过 | 跳过 | 状态 |
|------|--------|------|------|------|
| AI 服务单元 | 10 | 10 | 0 | ✅ |
| 内容 API 集成 | 6 | 6 | 2 | ✅ |
| 后端端总计 | 33 | 33 | 4 | ✅ |

### 接口示例
```bash
# 生成分镜头脚本（使用 Mock 数据）
curl -X POST http://localhost:8000/api/v1/content/generate-script \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI工具推荐",
    "platform": "douyin",
    "duration": 60,
    "style": "humorous"
  }'

# 改写逐字稿（需配置 AI）
curl -X POST http://localhost:8000/api/v1/content/rewrite-transcript \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "原始内容...",
    "style": "professional",
    "target_duration": 30
  }'

# 生成大纲（需配置 AI）
curl -X POST http://localhost:8000/api/v1/content/generate-outline \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "内容文本..."
  }'

# 流式生成分镜头脚本（需配置 AI）
curl -N -X POST http://localhost:8000/api/v1/content/generate-script-stream \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI工具推荐",
    "platform": "douyin",
    "duration": 60,
    "style": "humorous"
  }'

# 流式改写逐字稿（需配置 AI）
curl -N -X POST http://localhost:8000/api/v1/content/rewrite-transcript-stream \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "原始内容...",
    "style": "professional",
    "target_duration": 30
  }'
```

---

#### Phase 8.1: 流式输出改造 ✅
- ✅ 在 AIService 抽象基类添加 `generate_stream` 异步生成器方法
- ✅ 实现 AnthropicService、OpenAIService、ArkService 流式生成
- ✅ AIServiceManager 添加 `generate_stream` 方法
- ✅ 新增 `/generate-script-stream` 流式 API 端点
- ✅ 新增 `/rewrite-transcript-stream` 流式 API 端点
- ✅ 流式接口单元测试（test_generate_stream, test_generate_stream_unavailable_service）
- ✅ 流式接口集成测试（TestStreamingAPIWithoutAI, TestStreamingAPIWithRealAI）

### 测试结果（Phase 8.1）
| 类型 | 测试数 | 通过 | 跳过 | 状态 |
|------|--------|------|------|------|
| AI 服务单元 | 14 | 12 | 2 | ✅ |
| 内容 API 集成 | 12 | 8 | 4 | ✅ |
| 后端端总计 | 43 | 37 | 6 | ✅ |

### 流式接口使用方式
```javascript
// 前端流式调用示例
async function streamGenerateScript(data) {
  const response = await fetch('/api/v1/content/generate-script-stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const text = decoder.decode(value, { stream: true })
    if (text.includes('[STREAM_COMPLETE]')) break

    // 更新 UI 显示
    updateDisplay(text)
  }
}
```

---

#### Phase 9: 热点/对标数据源接入 ✅
- ✅ 创建平台数据获取模块 (`core/platform_api.py`)
- ✅ 实现 `HotTopicAPI` 类（支持微博、抖音、小红书）
- ✅ 实现 `CompetitorAPI` 类（支持抖音、小红书）
- ✅ 实现 `PlatformAPIManager` 管理器
- ✅ 更新 `TrendingService` 调用平台API
- ✅ 更新 `CompetitorService` 调用平台API
- ✅ 混合模式：优先真实API，失败降级到mock
- ✅ 添加 httpx 依赖到 requirements.txt
- ✅ 更新 .env.example 添加平台API配置说明
- ✅ 平台API单元测试（20个测试，全部通过）
- ✅ 平台API集成测试（15个测试，全部通过）

### 新增文件
```
backend/
├── core/platform_api.py         # 平台数据获取模块
├── tests/unit/test_platform_api.py         # 平台API单元测试
└── tests/integration/test_api_platform.py  # 平台API集成测试
```

### 环境变量配置
```bash
# 新榜API（微博、抖音、小红书热点）
XINBANG_API_KEY=your_xinbang_key

# 灰豚API（小红书数据）
HUITUN_API_KEY=your_huitun_key

# 注意：未配置时会自动使用mock数据
```

### 测试结果（Phase 9）
| 类型 | 测试数 | 通过 | 状态 |
|------|--------|------|------|
| 平台API单元 | 20 | 20 | ✅ |
| 平台API集成 | 15 | 15 | ✅ |
| 后端总计 | 72 | 72 | ✅ |

### API 接口示例
```bash
# 热点搜索（混合模式：优先真实API，失败降级mock）
curl -X POST http://localhost:8000/api/v1/trending/search \
  -H "Content-Type: application/json" \
  -d '{"keyword":"AI","platforms":["douyin","weibo"],"days":7}'

# 对标账号搜索（混合模式）
curl -X POST http://localhost:8000/api/v1/competitors/search \
  -H "Content-Type: application/json" \
  -d '{"niche":"科技","platforms":["douyin"]}'

# 导出对标账号Excel
curl -X GET "http://localhost:8000/api/v1/competitors/export?niche=美妆" \
  --output competitors.xlsx
```

### 数据源说明
- **默认行为**：未配置API密钥时，系统自动使用mock数据
- **降级策略**：API调用失败（超时、限流等）时自动降级到mock数据
- **支持的API**：
  - 新榜（微博、抖音、小红书）：https://open.newrank.cn/
  - 灰豚（小红书）：https://open.huitun.com/
- **扩展方式**：在 `platform_api.py` 中对应方法添加真实API调用逻辑

---

#### Phase 10: 音视频转写 ✅
- ✅ 创建转写引擎模块 (core/transcribe_engine.py)
- ✅ 实现 WhisperLocalEngine（本地 Whisper）
- ✅ 实现 AliyunEngine（阿里云语音识别，待实现 API）
- ✅ 实现 VolcengineEngine（火山引擎语音转写，待实现 API）
- ✅ 更新 media_processor.py 支持真实转写引擎
- ✅ 更新 media_service.py 支持引擎切换
- ✅ 更新配置 settings.py 添加转写引擎配置
- ✅ 更新 .env.example 添加转写引擎环境变量
- ✅ 更新 main.py 初始化转写引擎
- ✅ 更新 requirements.txt 添加 openai-whisper、torch、tqdm
- ✅ 修复 JSONColumn 兼容 SQLAlchemy 2.0
- ✅ 转写引擎单元测试（16个测试，全部通过）
- ✅ 媒体 API 集成测试（10个测试，9个通过，1个跳过）

### 新增文件
```
backend/
├── core/transcribe_engine.py          # 转写引擎抽象和实现
├── tests/unit/test_transcribe_engine.py # 转写引擎单元测试
└── tests/integration/test_api_media.py  # 媒体 API 集成测试
```

### 环境变量配置
```bash
# 转写引擎: whisper_local, aliyun, volcengine, mock
TRANSCRIBE_ENGINE=whisper_local

# Whisper配置（本地转写）
WHISPER_MODEL=base        # tiny, base, small, medium, large-v2, large-v3
WHISPER_LANGUAGE=zh       # 转写语言

# 阿里云语音识别配置
ALIYUN_ACCESS_KEY_ID=
ALIYUN_ACCESS_KEY_SECRET=
ALIYUN_APP_KEY=

# 火山引擎语音转写配置
VOLCENGINE_ACCESS_KEY=
VOLCENGINE_SECRET_ACCESS_KEY=
VOLCENGINE_APP_ID=

# 是否使用Mock转写（用于测试）
USE_MOCK_TRANSCRIBE=false
```

### 测试结果（Phase 10）
| 类型 | 测试数 | 通过 | 跳过 | 状态 |
|------|--------|------|------|------|
| 转写引擎单元 | 16 | 16 | 0 | ✅ |
| 媒体 API 集成 | 10 | 9 | 1 | ✅ |
| 后端总计 | 81 | 80 | 3 | ✅ |

### API 接口示例
```bash
# 上传音频文件
curl -X POST http://localhost:8000/api/v1/media/upload \
  -F "file=@/path/to/audio.mp3"

# 上传视频文件（会自动提取音频）
curl -X POST http://localhost:8000/api/v1/media/upload \
  -F "file=@/path/to/video.mp4"

# 获取任务状态和结果
curl http://localhost:8000/api/v1/media/task/{task_id}
```

### 转写引擎说明
- Whisper本地引擎：需要安装 ffmpeg 和 openai-whisper，支持离线转写
- 降级策略：转写引擎不可用时自动降级到 mock 数据
- 视频处理：上传视频时会使用 ffmpeg 提取音频再转写
- 时间戳支持：Whisper 返回分段时间戳
- 扩展方式：在 transcribe_engine.py 中实现 AliyunEngine/VolcengineEngine 的 transcribe 方法

---

#### Phase 11: 用户系统 + 配额管理 ✅
- ✅ 创建用户模型（UserTable：id, username, password_hash, email, quota_balance, created_at 等）
- ✅ 添加认证依赖（bcrypt, PyJWT）
- ✅ 实现 JWT 工具模块（core/jwt.py）
- ✅ 实现认证服务层（services/auth_service.py）
- ✅ 创建认证 API 路由（api/auth.py）
  - ✅ POST /api/v1/auth/register – 注册新用户
  - ✅ POST /api/v1/auth/login – 登录，返回 JWT token
  - ✅ GET /api/v1/auth/me – 获取当前用户信息（需认证）
  - ✅ GET /api/v1/auth/quota – 获取配额余额
  - ✅ POST /api/v1/auth/recharge – 充值配额
  - ✅ POST /api/v1/auth/admin/recharge – 管理员充值
  - ✅ GET /api/v1/auth/admin/users – 获取用户列表（管理员）
- ✅ 实现认证依赖（api/dependencies.py）
  - ✅ get_current_user – JWT 认证依赖
  - ✅ require_admin – 管理员权限检查
- ✅ 为现有资源接口添加了配额检查
- ✅ content.py – 生成脚本、改写逐字稿、生成大纲
- ✅ trending.py – 热点搜索
- ✅ competitors.py – 对标搜索
- ✅ media.py – 音视频上传转写
- ✅ 配额功能消耗
  - ✅ generate_script: 5 点
  - ✅ rewrite_transcript: 5 点
  - ✅ generate_outline: 3 点
  - ✅ search_trending: 2 点
  - ✅ search_competitors: 2 点
  - ✅ transcribe_audio: 10 点
  - ✅ transcribe_video: 10 点
- ✅ 更新 .env.example 添加 JWT_SECRET、DEFAULT_QUOTA 配置
- ✅ 认证服务单元测试（23 个测试通过）
- ✅ 添加用户领域模型（models/domain/user.py）

### 新增文件
```
backend/
├── core/jwt.py                      # JWT 工具模块
├── services/auth_service.py           # 认证服务层
├── api/dependencies.py               # 认证和配额依赖
├── api/auth.py                      # 认证 API 路由
├── models/domain/user.py             # 用户领域模型
└── tests/unit/test_auth_service.py  # 认证服务单元测试

# 数据库表更新
backend/models/database/tables.py        # 添加 UserTable
```

### 环境变量配置
```bash
# JWT 配置
JWT_SECRET=your-secret-key-change-in-production

# 用户默认配额
DEFAULT_QUOTA=100
```

### 依赖更新
```bash
# 新增认证和安全依赖
bcrypt>=4.0.0
PyJWT>=2.8.0
pydantic[email]>=2.0.0  # 邮箱验证
```

### 测试结果（Phase 11）
| 类型 | 测试数 | 通过 | 状态 |
|------|--------|------|------|
| 认证服务单元 | 23 | 23 | ✅ |

### API 接口示例
```bash
# 1. 注册新用户
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123456",
    "email": "test@example.com"
  }'

# 响应示例：
# {
#   "user": {"id": 1, "username": "testuser", "email": "test@example.com", "quota_balance": 100, "is_active": true, "created_at": "2026-03-27T..."},
#   "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
#   "message": "注册成功"
# }

# 2. 用户登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123456"
  }'

# 响应示例：
# {
#   "user": {"id": 1, "username": "testuser", "email": "test@example.com", "quota_balance": 100, ...},
#   "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
#   "message": "登录成功"
# }

# 3. 获取当前用户信息（需要认证）
TOKEN=<从登录响应获取的token>

curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 4. 获取配额余额
curl -X GET http://localhost:8000/api/v1/auth/quota \
  -H "Authorization: Bearer $TOKEN"

# 响应示例：
# {"user_id": 1, "balance": 100, "added": 0}

# 5. 充值配额
curl -X POST http://localhost:8000/api/v1/auth/recharge \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 50}'

# 响应示例：
# {"user_id": 1, "balance": 150, "added": 50}

# 6. 调用需要配额的接口（以内容生成为例）
curl -X POST http://localhost:8000/api/v1/content/generate-script \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI工具推荐",
    "platform": "douyin",
    "duration": 60,
    "style": "humorous"
  }'

# 配额不足时返回 403：
# {
#   "detail": {
#     "code": "quota_exceeded",
#     "message": "配额不足，此操作需要 5 点，当前余额: 0"
#   }
# }
```

### 配额消耗说明
| 功能 | 消耗点数 | 说明 |
|------|----------|------|
| generate_script | 5 | 生成分镜头脚本 |
| rewrite_transcript | 5 | 改写逐字稿 |
| generate_outline | 3 | 生成大纲 |
| search_trending | 2 | 搜索热点 |
| search_competitors | 2 | 搜索对标账号 |
| transcribe_audio | 10 | 音频转写 |
| transcribe_video | 10 | 视频转写 |

### 认证流程
1. 用户注册：创建账号，设置初始配额（默认 100 点）
2. 用户登录：验证用户名和密码，返回 JWT token
3. 访问受保护接口：在请求头中携带 `Authorization: Bearer <token>`
4. 配额检查：调用消耗资源的接口前自动检查余额
5. 配额扣减：请求成功后自动扣减相应配额

### 安全说明
- 密码使用 bcrypt 哈希存储，不可逆
- JWT token 默认有效期 24 小时
- 管理员接口需要 is_admin=true 的用户权限
- 未认证访问受保护接口返回 401
- 配额不足返回 403

---

#### Phase 12: 发布日历 + 数据导入导出 ✅
- ✅ 创建数据库表 `CalendarEvent`（id, user_id, title, content, scheduled_date, platform, status, created_at, updated_at）
- ✅ 创建日历领域模型（CalendarEventCreate, CalendarEventUpdate, CalendarEventResponse, CalendarEventListRequest）
- ✅ 实现日历服务层（CRUD 操作）
- ✅ 实现日历 API 路由
  - ✅ POST /api/v1/calendar/events – 创建日历事件
  - ✅ GET /api/v1/calendar/events/{id} – 获取单个事件
  - ✅ GET /api/v1/calendar/events – 获取事件列表（支持日期范围和状态筛选）
  - ✅ PUT /api/v1/calendar/events/{id} – 更新事件
  - ✅ DELETE /api/v1/calendar/events/{id} – 删除事件
  - ✅ GET /api/v1/calendar/events/upcoming – 获取未来指定天数内的事件
- ✅ 实现导入导出服务层（ImportExportService）
- ✅ 添加导出端点到 trending 和 competitors（支持 csv/xlsx 格式）
- ✅ 创建导入 API 路由
  - ✅ POST /api/v1/import/trending – 导入热点话题
  - ✅ POST /api/v1/import/competitors – 导入对标账号
  - ✅ POST /api/v1/import/calendar – 导入日历事件

### 新增文件
```
backend/
├── models/
│   └── domain/
│       └── calendar.py                      # 日历领域模型
├── models/database/
│   └── tables.py                            # 添加 CalendarEventTable
├── services/
│   ├── calendar_service.py                   # 日历服务层
│   └── import_export_service.py            # 导入导出服务层
└── api/
    ├── calendar.py                            # 日历 API 路由
    └── data_import.py                          # 导入 API 路由
```

### 环境变量配置
```bash
# 无新增环境变量
```

### 测试结果（Phase 12）
| 类型 | 测试数 | 通过 | 跳过 | 状态 |
|------|--------|------|------|------|
| 日历服务单元 | 11 | 11 | 0 | ✅ |
| 导入导出服务单元 | 15 | 12 | 3 | ✅ |
| 后端总计 | 105 | 97 | 8 | ✅ |

### API 接口示例

#### 日历 API
```bash
# 1. 创建日历事件
curl -X POST http://localhost:8000/api/v1/calendar/events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "发布短视频",
    "content": "脚本内容",
    "scheduled_date": "2026-04-01T12:00:00",
    "platform": "douyin",
    "status": "pending"
  }'

# 2. 获取日历事件列表
curl -X GET "http://localhost:8000/api/v1/calendar/events?start_date=2026-04-01&end_date=2026-04-30" \
  -H "Authorization: Bearer $TOKEN"

# 3. 获取单个事件
curl -X GET http://localhost:8000/api/v1/calendar/events/1 \
  -H "Authorization: Bearer $TOKEN"

# 4. 更新事件
curl -X PUT http://localhost:8000/api/v1/calendar/events/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "更新后的标题",
    "status": "completed"
  }'

# 5. 删除事件
curl -X DELETE http://localhost:8000/api/v1/calendar/events/1 \
  -H "Authorization: Bearer $TOKEN"

# 6. 获取未来事件（7天内）
curl -X GET http://localhost:8000/api/v1/calendar/events/upcoming?days=7 \
  -H "Authorization: Bearer $TOKEN"
```

#### 导出 API
```bash
# 导出热点话题（CSV 格式）
curl -X GET "http://localhost:8000/api/v1/trending/export?keyword=AI&format=csv" \
  -H "Authorization: Bearer $TOKEN" \
  --output hot_topics.csv

# 导出热点话题（Excel 格式）
curl -X GET "http://localhost:8000/api/v1/trending/export?keyword=AI&format=xlsx" \
  -H "Authorization: Bearer $TOKEN" \
  --output hot_topics.xlsx

# 导出对标账号
curl -X GET "http://localhost:8000/api/v1/competitors/export?niche=科技&format=csv" \
  -H "Authorization: Bearer $TOKEN" \
  --output competitors.csv
```

#### 导入 API
```bash
# 导入热点话题（CSV 文件）
curl -X POST http://localhost:8000/api/v1/import/trending \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@hot_topics.csv"

# 导入对标账号（CSV 文件）
curl -X POST http://localhost:8000/api/v1/import/competitors \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@competitors.csv"

# 导入日历事件（CSV 文件）
curl -X POST http://localhost:8000/api/v1/import/calendar \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@calendar_events.csv"
```

### 日历事件状态说明
- `pending`: 待处理（默认）
- `in_progress`: 进行中
- `completed`: 已完成
- `cancelled`: 已取消

### 导入导出功能说明
- **支持的文件格式**: CSV、XLSX
- **导出格式**: CSV（默认）、XLSX
- **热点话题导出**: 关键词、平台、热度值、趋势
- **对标账号导出**: 用户名、平台、赛道、粉丝数、点赞数、作品数
- **日历事件导入**: 标题、计划日期、内容、平台、状态
- **无需配额**: 导入导出操作不消耗用户配额

---

#### Phase 13: 部署上线 ✅
- ✅ 更新 docker-compose.yml 完整环境变量配置
- ✅ 更新 backend/Dockerfile 添加 ffmpeg 依赖
- ✅ 创建部署文档 DEPLOY.md（完整部署指南）
- ✅ 创建一键部署脚本 deploy.sh（Linux/mac）
- ✅ 创建一键部署脚本 deploy.ps1（Windows）

### 部署文件
```
MediaPilot/
├── DEPLOY.md                # 部署文档
├── deploy.sh               # Linux/Mac 一键部署脚本
├── deploy.ps1             # Windows 一键部署脚本
├── docker-compose.yml       # 容器编排配置（已更新环境变量）
├── .env.example           # 环境变量示例
├── backend/
│   └── Dockerfile          # 已添加 ffmpeg 依赖
└── web/
    └── nginx.conf          # Nginx 配置
```

### 快速部署步骤
```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 填入实际值

# 2. 一键部署（自动构建和启动）
# Linux/Mac
bash deploy.sh

# Windows
powershell -ExecutionPolicy Bypass -File deploy.ps1

# 3. 访问服务
# 前端: http://localhost
# 后端: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 部署验证
```bash
# 健康检查
curl http://localhost:8000/health     # {"status":"healthy"}
curl http://localhost:80/health          # healthy

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 生产环境部署
详见本文档"部署指南"部分，包含：
- 环境要求（Docker、Nginx 等）
- SSL/HTTPS 配置
- 反向代理配置
- 数据库初始化
- 监控和日志收集
- 备份和恢复策略
- 故障排查指南

---

## 今日目标（2026-03-31）

### 优先任务

#### 1. 修复 AI 功能 404 错误（🔴 高优先级）
- ✅ 已添加 `/api/ai/stream` 路由（backend/api/ai_chat.py）
- ✅ 已推送到 GitHub（commit: 80f5c34）
- ⏳ 等待 Vercel 重新部署验证
- ⏳ 测试热点搜索功能是否正常

#### 2. 实现本地自动启动方案（✅ 已完成）
- ✅ 端口已固定（前端 5173，后端 8000）
- ✅ 创建一键启动脚本（启动前后端）
  - start.bat（Windows：前后端分开窗口启动）
  - start-backend.bat（仅后端）
  - start-frontend.bat（仅前端）
  - start-local.ps1（Windows PowerShell）
  - start-local.sh（Linux/Mac）
- ✅ 使用 Docker 一键启动（deploy.sh / deploy.ps1）
- ✅ 开机自启动配置
  - setup-autostart-docker.bat（Docker 容器自启动，需管理员权限）
  - setup-autostart-service.bat（Windows 服务自启动，需管理员权限）

#### 3. 测试各功能（🟡 中优先级）
- ⏳ 热点搜索
- ⏳ 对标分析
- ⏳ 脚本生成
- ⏳ 音视频转写
- ⏳ 内容日历
- ⏳ 数据导入导出

### 后续规划
- [ ] 云服务器 24/7 部署（需要购买云服务器）
- [ ] 移动端开发（Flutter）
- [ ] 桌面端开发（PyQt5）
- [ ] 浏览器扩展开发
- [ ] 新增日常功能（待用户描述具体需求）
