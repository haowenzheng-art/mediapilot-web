# MediaPilot 企业级重构计划 v2.0.0-alpha

> **状态**: 规划中  
> **制定日期**: 2026-06-15  
> **目标版本**: v2.0.0-alpha  
> **适用范围**: 后端 `backend/` + 前端 `web/`

---

## 1. 概述

MediaPilot 当前处于 v1.x Demo 阶段——功能原型已跑通，热点搜索、文案生成、脚本生成、订阅推送等核心链路均可使用，但代码组织方式仍停留在「可运行」层面，距离企业级「可维护、可扩展、可观测」还有显著差距。

本次重构的目标是：

1. **修复工程基座**：消除 `sys.path` 黑魔法、统一配置管理、补齐数据库迁移
2. **提升性能与韧性**：异步化改造、引入 Redis + 任务队列
3. **启动 Agent 架构**：将现有 AI 能力封装为 Tool，搭建 ReAct Agent 框架

所有重构严格遵循当前已有的三层架构（API → Service → Repository），不做结构性打乱。

---

## 2. 审计发现的问题清单

| # | 严重级别 | 问题描述 | 影响文件 | 影响范围 |
|---|---------|---------|---------|---------|
| 1 | **P0-致命** | `sys.path.insert` 滥用（40+ 处） | 几乎全部 `.py` 文件 | 无法 `pip install`、循环导入风险、打包失败 |
| 2 | **P0-致命** | 无 Alembic 迁移文件，`create_all()` 全量建表 | `backend/config/database.py` | 生产环境无法增量更新 schema |
| 3 | **P0-安全** | 开发后门 `get_dev_user()` 硬编码绕过认证 | 6 个路由文件 + `dependencies.py` | 任何部署环境都无认证保护 |
| 4 | **P1-严重** | 配置管理分散（3 处各自 `os.getenv`） | `main.py` / `config/database.py` / `config/settings.py` | 配置不一致，难以维护 |
| 5 | **P1-严重** | 内存存储替代数据库（`_copywritings={}`, `tasks={}`） | `copywriting_service.py` / `api/routes.py` | 重启即丢失数据 |
| 6 | **P1-严重** | 异步/同步混用，AI 调用阻塞事件循环 | `copywriting_service.py` / `ai_service.py` | 并发性能差，长请求超时 |
| 7 | **P1-严重** | 速率限制中间件已写好但未注册 | `middleware/rate_limiting.py` | API 无防滥用保护 |
| 8 | **P2-中等** | CORS 配置为 `allow_origins=["*"]` | `main.py:114-120` | 生产环境安全风险 |
| 9 | **P2-中等** | JWT Secret 使用默认值 `"your-secret-key-change-in-production"` | `backend/core/jwt.py` | 令牌可伪造 |
| 10 | **P2-中等** | 重复的服务文件（`auth_service.py` + `auth_service_typed.py`，`trending_service.py` + `trending_service_typed.py`，`mock_data.py` + `mock_data_typed.py`） | `backend/services/` | 维护混乱，不知该用哪个 |
| 11 | **P2-中等** | 废弃文件残留（`routes.py`, `routes_new.py`, `data_import_fixed.py`, `main_full.py`, `main_simple.py`, `simple_backend.py`） | `backend/api/` + `backend/` | 代码混淆 |
| 12 | **P3-轻微** | 前端使用 state-based 路由而非 react-router | `web/src/App.jsx` | 无法 URL 分享、SEO 差 |
| 13 | **P3-轻微** | 无结构化日志（ELK/Loki 友好格式） | 全部日志 | 线上排查困难 |
| 14 | **P3-轻微** | 测试覆盖率未设门槛，无 CI 自动执行 | `.github/workflows/ci.yml`（存在但未完善） | 重构易引入回归 |

---

## 3. 分阶段执行计划

### 阶段一：工程基座修复（预计 3-4 天）

---

#### 任务 1：导入系统标准化

**目标**: 消除所有 `sys.path.insert`，改用标准 Python 包导入。

**前置条件**: 补全所有包的 `__init__.py`。

**执行步骤**:

1. 扫描所有 `sys.path.insert` 调用，建立受影响文件清单
2. 为以下目录补全 `__init__.py`（如缺失）：
   - `backend/api/` — 已有，需检查
   - `backend/services/` — 已有，需检查
   - `backend/models/` — 已有
   - `backend/models/database/` — 已有
   - `backend/models/domain/` — 已有
   - `backend/models/schemas/` — 已有
   - `backend/repository/` — 已有
   - `backend/scrapers/` — 已有
   - `backend/core/` — 已有
   - `backend/config/` — 已有
   - `backend/middleware/` — **需新建**
   - `backend/utils/` — 已有
   - `backend/tests/` — 已有
   - `backend/tests/unit/` — 已有
   - `backend/tests/integration/` — 已有
3. 将所有 `sys.path.insert(0, ...)` 替换为标准导入：
   ```python
   # Before
   sys.path.insert(0, project_root)
   from backend.services.copywriting_service import copywriting_service
   
   # After
   from backend.services.copywriting_service import copywriting_service
   ```
4. 处理 `shared/` 目录的导入（如有跨目录引用）
5. 验证：`python -c "from backend.main import app"` 能正常导入

**完成标准**:
- [ ] `grep -r "sys.path.insert" backend/` 结果为空（排除测试 fixture）
- [ ] `python -m backend.main --help` 能正常启动
- [ ] 所有 `from backend.xxx` 导入不再报 ModuleNotFoundError

---

#### 任务 2：配置管理统一

**目标**: 单一配置源，所有模块通过 `settings` 获取。

**执行步骤**:

1. 重写 `backend/config/settings.py`，使用 `pydantic-settings`:
   ```python
   from pydantic_settings import BaseSettings
   from functools import lru_cache
   
   class Settings(BaseSettings):
       # 服务
       API_HOST: str = "127.0.0.1"
       API_PORT: int = 8000
       
       # 数据库
       DATABASE_URL: str = "sqlite:///./mediapilot.db"
       
       # 认证
       JWT_SECRET: str = "change-me-in-production"
       DEV_MODE: bool = True
       
       # AI
       AI_PROVIDER: str = "openai"
       AI_API_KEY: str = ""
       AI_BASE_URL: str = "https://apihub.agnes-ai.com/v1"
       AI_MODEL: str = "agnes-2.0-flash"
       AI_TIMEOUT: int = 60
       AI_MAX_RETRIES: int = 3
       
       # 配额
       DEFAULT_QUOTA: int = 100
       
       # 爬虫/API
       XINBANG_API_KEY: str = ""
       HUITUN_API_KEY: str = ""
       
       # 转写
       TRANSCRIBE_ENGINE: str = "whisper_local"
       USE_MOCK_TRANSCRIBE: bool = False
       WHISPER_MODEL: str = "base"
       WHISPER_LANGUAGE: str = "zh"
       
       # CORS
       CORS_ORIGINS: list[str] = ["http://localhost:5173"]
       
       # 日志
       LOG_LEVEL: str = "INFO"
       
       class Config:
           env_file = ".env"
           env_file_encoding = "utf-8"
   
   @lru_cache
   def get_settings() -> Settings:
       return Settings()
   ```

2. 全局替换 `os.getenv("XXX")` → `get_settings().XXX`
3. 在 `main.py` 中移除手动 `load_dotenv` 和重复的环境变量读取
4. 添加 `DEV_MODE` 开关控制开发后门行为
5. 更新 `.env.example` 使其与 Settings 字段完全对齐
6. 清理 `config/database.py`，改为从 `settings.DATABASE_URL` 读取

**完成标准**:
- [ ] `backend/config/settings.py` 是唯一配置来源
- [ ] 无其他地方使用 `os.getenv` 读取业务配置
- [ ] `.env.example` 覆盖所有可配置项
- [ ] `DEV_MODE=True` 时启用 dev user，`False` 时强制 JWT 认证

---

#### 任务 3：数据库迁移（Alembic）

**目标**: 建立完整的数据库迁移工作流。

**执行步骤**:

1. 在项目根目录初始化 Alembic:
   ```bash
   alembic init backend/alembic
   ```
2. 配置 `alembic.ini`:
   - `sqlalchemy.url` 从环境变量读取
3. 配置 `env.py`:
   - 导入 `backend.models.database.base.Base`
   - 导入所有模型表（确保 `create_all()` 能找到）
4. 生成初始迁移:
   ```bash
   alembic revision --autogenerate -m "initial schema"
   alembic upgrade head
   ```
5. 验证迁移结果:
   - 检查生成的表结构与 `models/database/tables.py` 一致
   - 确认索引、外键正确
6. 将 `main.py` 中的 `init_db()` → 改为调用 `alembic upgrade head`
7. 新增 `TaskStatus` 模型替代内存 `tasks: Dict` 和 `_copywritings: Dict`

**TaskStatus 模型设计**:
```python
class TaskStatusTable(Base):
    __tablename__ = "task_statuses"
    
    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_type = Column(String(50), nullable=False)  # copywriting, transcription, media_process
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    result = Column(JSONColumn, nullable=True)  # AI 生成结果
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

8. 迁移 `copywriting_service._copywritings` → 写入 `TaskStatusTable`
9. 迁移 `routes.py tasks dict` → 写入 `TaskStatusTable`

**完成标准**:
- [ ] `alembic history` 显示初始迁移
- [ ] `alembic upgrade head` 成功执行
- [ ] 所有内存存储已迁移到数据库
- [ ] 新增 `alembic revision` 能自动生成 schema 变更

---

#### 任务 4：中间件与安全加固

**目标**: 注册速率限制、收紧 CORS、关闭开发后门。

**执行步骤**:

1. 在 `api/__init__.py` 的 `register_routes()` 中，改为条件注册速率限制:
   ```python
   if settings.DEV_MODE:
       # 开发模式：不启用严格限流
       pass
   else:
       app.middleware("http")(create_rate_limiting_middleware())
   ```

2. 修改 `main.py` CORS 配置:
   ```python
   # Before
   app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
   
   # After
   origins = settings.CORS_ORIGINS if not settings.DEV_MODE else ["*"]
   app.add_middleware(CORSMiddleware, allow_origins=origins, ...)
   ```

3. 改造 `dependencies.py` 的 `get_current_user()`:
   ```python
   async def get_current_user(...):
       if settings.DEV_MODE:
           return get_or_create_dev_user(db)
       # 正式模式：强制 JWT 验证
       credentials = await security(request)
       if not credentials:
           raise HTTPException(status_code=401, detail="未提供认证令牌")
       user_id = get_user_id_from_token(credentials.credentials)
       user = db.query(UserTable).filter(UserTable.id == user_id).first()
       if not user or not user.is_active:
           raise HTTPException(status_code=401, detail="用户不存在或已禁用")
       return user
   ```

4. 改造所有路由中的 `get_dev_user()` → 统一使用 `dependencies.get_current_user()`
5. 清理重复服务文件:
   - 删除 `auth_service.py`，保留 `auth_service_typed.py`
   - 删除 `trending_service.py`，保留 `trending_service_typed.py`
   - 删除 `mock_data.py`，保留 `mock_data_typed.py`
6. 清理废弃文件:
   - `routes.py`（旧版，已被各独立路由替代）
   - `routes_new.py`
   - `data_import_fixed.py`
   - `main_full.py`
   - `main_simple.py`
   - `simple_backend.py`
   - `trending.py.bak`

**完成标准**:
- [ ] 生产模式下无 JWT 无法访问任何业务接口
- [ ] 速率限制中间件已注册并生效
- [ ] CORS 仅允许配置的源
- [ ] 重复文件和废弃文件已清理
- [ ] 所有路由不再有自己的 `get_dev_user()`

---

### 阶段二：性能与韧性提升（预计 2-3 天）

---

#### 任务 5：异步化改造

**目标**: 消除阻塞调用，全面支持 async/await。

**执行步骤**:

1. `ai_service.py` — 确保所有 AI 调用使用异步客户端:
   - `AnthropicService`: 使用 `anthropic.AsyncAnthropic`
   - `OpenAIService`: 使用 `AsyncOpenAI`（已有）
   - `ArkService`: 使用 `httpx.AsyncClient`（已有）
   - 移除同步的 `generate()` 方法或改为调用 `async_generate()`

2. `copywriting_service.py`:
   - 删除同步 `generate()` 方法，只保留 `generate_async()`
   - 删除 `rewrite()` 中的同步 AI 调用
   - 所有 `_build_prompt` 调用改为 await

3. `shoot_script_service.py`:
   - 检查是否也有同步/异步双版本，统一为异步

4. `trending_service.py`:
   - 确认 `search()` 是 `async def`（已是）
   - 爬虫调用链全部 async（确认）

5. `platform_api.py`:
   - `HotTopicAPI` 已使用 `httpx.AsyncClient`，确认无阻塞调用

6. `main.py` startup event:
   - `init_db()` 改为 `async with engine.begin():` 或在 `asyncio.to_thread()` 中执行

**完成标准**:
- [ ] 所有服务层方法签名统一为 `async def`
- [ ] 无 `time.sleep()` 阻塞调用（改用 `asyncio.sleep()`）
- [ ] AI 调用使用异步客户端
- [ ] `copywriting_service` 不再有同步 `generate()` 方法

---

#### 任务 6：任务队列引入（Redis + ARQ）

**目标**: 将耗时操作（AI 生成、爬虫、转写）放入后台任务队列。

**执行步骤**:

1. `docker-compose.yml` 添加 Redis 服务:
   ```yaml
   services:
     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
       volumes:
         - redis_data:/data
       healthcheck:
         test: ["CMD", "redis-cli", "ping"]
   
   volumes:
     redis_data:
   ```

2. 安装依赖:
   ```
   arq>=0.25.0
   redis>=5.0.0
   ```

3. 创建 `backend/tasks/` 目录:
   ```
   backend/tasks/
   ├── __init__.py
   ├── worker.py        # ARQ Worker 配置
   ├── jobs.py          # 任务函数定义
   └── serializers.py   # 任务参数序列化
   ```

4. `worker.py`:
   ```python
   from arq import create_pool
   from redis import Redis
   
   def get_redis_pool():
       return create_pool(Redis.from_url("redis://localhost:6379/0"))
   
   WORKER_SETTINGS = {
       "functions": ["run_copywriting_generation", "run_trending_search", "run_transcription"],
       "max_jobs": 10,
       "job_timeout": 300,  # 5分钟
       "retry_jobs": True,
       "max_tries": 3,
   }
   ```

5. `jobs.py` — 将耗时操作改为后台任务:
   - `run_copywriting_generation`: 接收 topic/persona/mode，写入 TaskStatusTable
   - `run_trending_search`: 接收 keyword/platforms，写入 TaskStatusTable
   - `run_transcription`: 接收 file_id，写入 TaskStatusTable

6. API 路由改造:
   - POST `/copywriting/generate` → 提交任务 → 返回 `task_id` → 前端轮询 GET `/tasks/{task_id}`
   - POST `/trending/search` → 提交任务 → 返回 `task_id`
   - 保留同步调用作为快速路径（轻量操作如配额检查）

7. 添加任务状态查询 API:
   ```python
   @router.get("/tasks/{task_id}")
   async def get_task_status(task_id: str, db: Session = Depends(get_db)):
       task = db.query(TaskStatusTable).filter(TaskStatusTable.id == task_id).first()
       if not task:
           raise HTTPException(404, "任务不存在")
       return success_response(data={"status": task.status, "result": task.result})
   ```

**完成标准**:
- [ ] Redis 在 docker-compose 中可用
- [ ] ARQ Worker 随应用启动
- [ ] AI 生成/爬虫/转写均为后台任务
- [ ] 前端有任务状态轮询机制
- [ ] 任务失败有重试和错误通知

---

### 阶段三：Agent 架构启动（预计 3-4 天）

---

#### 任务 7：Tool 抽象层

**目标**: 将现有 AI 能力封装为可被 Agent 调用的 Tool。

**执行步骤**:

1. 创建 `backend/agent/` 目录:
   ```
   backend/agent/
   ├── __init__.py
   ├── base.py          # Tool 抽象基类
   ├── registry.py      # ToolRegistry
   ├── tools/
   │   ├── __init__.py
   │   ├── search_trending_tool.py
   │   ├── copywriting_tool.py
   │   ├── scrape_tool.py
   │   └── export_tool.py
   └── models.py        # Agent 数据模型
   ```

2. `base.py` — Tool 接口定义:
   ```python
   from abc import ABC, abstractmethod
   from pydantic import BaseModel
   
   class ToolParam(BaseModel):
       name: str
       description: str
       type: str
       required: bool = False
   
   class ToolResult(BaseModel):
       success: bool
       content: str
       error: Optional[str] = None
       metadata: Optional[dict] = None
   
   class Tool(ABC):
       @property
       @abstractmethod
       def name(self) -> str: ...
       
       @property
       @abstractmethod
       def description(self) -> str: ...
       
       @property
       @abstractmethod
       def parameters(self) -> list[ToolParam]: ...
       
       @abstractmethod
       async def execute(self, **kwargs) -> ToolResult: ...
       
       def to_openai_function(self) -> dict:
           """转换为 OpenAI function calling 格式"""
           return {
               "name": self.name,
               "description": self.description,
               "parameters": {
                   "type": "object",
                   "properties": {p.name: {"type": p.type, "description": p.description} for p in self.parameters},
                   "required": [p.name for p in self.parameters if p.required],
               },
           }
   ```

3. 实现三个核心 Tool:
   - `SearchTrendingTool`: 调用 `TrendingService.search()`
   - `CopywritingTool`: 调用 `CopywritingService.generate_async()`
   - `ScrapeContentTool`: 调用 `ContentReferenceScraper`

4. `registry.py` — Tool 注册与管理:
   ```python
   class ToolRegistry:
       _tools: dict[str, Tool] = {}
       
       @classmethod
       def register(cls, tool: Tool): ...
       @classmethod
       def get(cls, name: str) -> Tool: ...
       @classmethod
       def list_all(cls) -> list[Tool]: ...
       @classmethod
       def to_openai_functions(cls) -> list[dict]: ...
   ```

5. 启动时自动注册所有 Tool:
   ```python
   # agent/__init__.py
   from .tools.search_trending_tool import SearchTrendingTool
   from .tools.copywriting_tool import CopywritingTool
   from .tools.scrape_tool import ScrapeContentTool
   from .registry import ToolRegistry
   
   ToolRegistry.register(SearchTrendingTool())
   ToolRegistry.register(CopywritingTool())
   ToolRegistry.register(ScrapeContentTool())
   ```

**完成标准**:
- [ ] `Tool` 抽象基类定义清晰，继承简单
- [ ] 至少 3 个 Tool 实现并通过单元测试
- [ ] `ToolRegistry` 支持注册/查询/列出/OpenAI 格式导出
- [ ] `to_openai_function()` 输出格式符合 OpenAI function calling 规范

---

#### 任务 8：Agent 执行器

**目标**: 实现 ReAct 循环，让 LLM 自主选择和调用 Tool。

**执行步骤**:

1. 在 `backend/agent/` 中添加 `executor.py`:
   ```python
   class AgentExecutor:
       """ReAct Agent 执行器"""
       
       def __init__(self, tool_registry: ToolRegistry, ai_manager: AIServiceManager):
           self.tools = tool_registry
           self.ai = ai_manager
           self.max_iterations = 10
           self.message_history: list[dict] = []
       
       async def run(self, user_input: str) -> AgentResult:
           """执行 ReAct 循环"""
           self.message_history = [
               {"role": "system", "content": self._build_system_prompt()},
               {"role": "user", "content": user_input},
           ]
           
           for iteration in range(self.max_iterations):
               # 1. 调用 LLM 获取下一步决策
               response = await self._call_llm_with_tools(
                   messages=self.message_history,
                   tools=self.tools.to_openai_functions()
               )
               
               # 2. 判断是否有工具调用
               if response.tool_calls:
                   # 3. 执行工具
                   for tc in response.tool_calls:
                       result = await self._execute_tool(tc)
                       self.message_history.append({
                           "role": "tool",
                           "tool_call_id": tc.id,
                           "content": result.model_dump_json(),
                       })
                   continue
               
               # 4. 最终答案
               return AgentResult(
                   answer=response.content,
                   iterations=iteration + 1,
                   tool_calls_used=[tc.function.name for tc in response.tool_calls] if response.tool_calls else [],
               )
           
           # 5. 防止死循环
           return AgentResult(
               answer="抱歉，我无法完成这个请求。",
               error="max_iterations_exceeded",
           )
   ```

2. 创建 Agent API 路由 `backend/api/agent.py`:
   ```python
   @router.post("/agent/run")
   async def run_agent(request: AgentRequest):
       """同步执行 Agent"""
       executor = AgentExecutor(tool_registry, ai_manager)
       result = await executor.run(request.prompt)
       return success_response(data=result.model_dump())
   
   @router.post("/agent/stream")
   async def run_agent_stream(request: AgentRequest):
       """SSE 流式输出 Agent"""
       ...
   ```

3. 添加系统 Prompt 模板:
   ```python
   SYSTEM_PROMPT = """你是一个新媒体内容创作助手。
   你可以使用以下工具完成任务：
   - search_trending: 搜索全网热点
   - copywriting: 生成口播文案
   - scrape_content: 抓取网页内容
   
   请用 ReAct 模式思考：观察(Observation) → 思维(Thought) → 行动(Action) → 结果(Observation)"""
   ```

4. 安全防护:
   - `max_iterations=10` 防止死循环
   - 单次 Agent 运行总超时 120 秒
   - 工具调用结果截断（单工具输出不超过 4000 tokens）
   - 记录完整 Agent 日志供审计

**完成标准**:
- [ ] Agent 能自主调用至少 2 个 Tool 完成复合任务
- [ ] SSE 流式输出正常工作
- [ ] max_iterations 保护生效（连续 10 次工具调用后强制终止）
- [ ] 有 `/api/v1/agent/run` 和 `/api/v1/agent/stream` 两个端点
- [ ] Agent 执行日志可追踪

---

## 4. 检查清单

### 任务 1：导入系统标准化
- [ ] 扫描所有 `sys.path.insert`，统计数量
- [ ] 补全 `backend/middleware/__init__.py`
- [ ] 批量替换为 `from backend.xxx` 绝对导入
- [ ] 验证 `python -m backend.main` 正常启动
- [ ] 验证测试套件全部通过

### 任务 2：配置管理统一
- [ ] 安装 `pydantic-settings`
- [ ] 重写 `backend/config/settings.py`
- [ ] 替换所有 `os.getenv()` 调用
- [ ] `main.py` 移除手动 dotenv 加载
- [ ] 更新 `.env.example`
- [ ] 添加 `DEV_MODE` 开关
- [ ] 验证各模式（dev/prod）配置正确

### 任务 3：数据库迁移
- [ ] `alembic init backend/alembic`
- [ ] 配置 `alembic.ini` 和 `env.py`
- [ ] 生成初始迁移 `alembic revision --autogenerate`
- [ ] 创建 `TaskStatusTable` 模型
- [ ] 迁移 `copywriting_service._copywritings` → DB
- [ ] 迁移 `routes.py tasks dict` → DB
- [ ] 验证 `alembic upgrade head` 和 `alembic downgrade`

### 任务 4：中间件与安全
- [ ] 注册速率限制中间件
- [ ] 收紧 CORS 配置
- [ ] 改造 `dependencies.py` 统一认证
- [ ] 删除所有路由中的 `get_dev_user()`
- [ ] 清理重复服务文件
- [ ] 清理废弃文件
- [ ] 验证生产模式无后门

### 任务 5：异步化改造
- [ ] `ai_service.py` 全部使用异步客户端
- [ ] `copywriting_service.py` 删除同步方法
- [ ] `shoot_script_service.py` 统一异步
- [ ] 检查所有 `time.sleep()` → `asyncio.sleep()`
- [ ] 压力测试验证并发性能

### 任务 6：任务队列
- [ ] docker-compose 添加 Redis
- [ ] 安装 arq + redis
- [ ] 创建 `backend/tasks/` 目录和 worker
- [ ] 实现后台任务函数
- [ ] API 改为提交任务 + 状态轮询
- [ ] 前端添加任务状态 UI

### 任务 7：Tool 抽象层
- [ ] 定义 `Tool` 基类和 `ToolResult`
- [ ] 实现 `SearchTrendingTool`
- [ ] 实现 `CopywritingTool`
- [ ] 实现 `ScrapeContentTool`
- [ ] 实现 `ToolRegistry`
- [ ] 单元测试覆盖所有 Tool

### 任务 8：Agent 执行器
- [ ] 实现 `AgentExecutor` ReAct 循环
- [ ] 添加 `max_iterations` 保护
- [ ] 实现 `/agent/run` 同步端点
- [ ] 实现 `/agent/stream` SSE 端点
- [ ] 编写 Agent 系统 Prompt
- [ ] 端到端测试：用户输入 → Agent 自主调用工具 → 返回结果

---

## 5. CI/CD 与测试要求

### GitHub Actions 流水线

```yaml
# .github/workflows/ci.yml（需增强）
name: CI

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff
      - run: ruff check backend/
      - run: ruff format --check backend/

  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ --cov=backend --cov-fail-under=70 --cov-report=xml
      - uses: codecov/codecov-action@v4

  build:
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v4
      - run: docker compose -f docker-compose.yml build backend
```

### 测试覆盖率目标

| 层级 | 最低覆盖率 | 说明 |
|------|-----------|------|
| `backend/config/` | 90% | 配置必须可靠 |
| `backend/core/ai_service.py` | 80% | AI 调用是核心 |
| `backend/services/` | 75% | 业务逻辑 |
| `backend/api/` | 60% | 路由层以集成测试为主 |
| `backend/agent/` | 80% | 新模块，需高覆盖 |
| 整体 | 70% | 阶段性目标 |

### 测试要求

- [ ] 每个新增 Tool 必须有单元测试
- [ ] Agent Executor 必须有端到端测试（mock AI 响应）
- [ ] 所有 API 路由必须有集成测试（使用 test client）
- [ ] 数据库迁移必须有回滚测试
- [ ] 认证流程必须有 JWT 签发/验证/刷新测试

---

## 6. 参考附件

### 关键文件路径

| 类别 | 文件路径 |
|------|---------|
| 应用入口 | `backend/main.py` |
| 路由注册 | `backend/api/__init__.py` |
| 配置 | `backend/config/settings.py`, `backend/config/database.py` |
| AI 服务 | `backend/core/ai_service.py` |
| 转写引擎 | `backend/core/transcribe_engine.py` |
| 认证 | `backend/api/auth.py`, `backend/services/auth_service_typed.py`, `backend/core/jwt.py` |
| 依赖注入 | `backend/api/dependencies.py` |
| 速率限制 | `backend/middleware/rate_limiting.py` |
| 文案服务 | `backend/services/copywriting_service.py` |
| 热点服务 | `backend/services/trending_service.py` |
| 脚本服务 | `backend/services/shoot_script_service.py` |
| 订阅服务 | `backend/services/subscription_service.py` |
| 内容库服务 | `backend/services/content_library_service.py` |
| 数据库模型 | `backend/models/database/tables.py`, `backend/models/database/base.py` |
| 领域模型 | `backend/models/domain/*.py` |
| API 路由 | `backend/api/copywriting.py`, `backend/api/trending.py`, `backend/api/shoot_script.py` |
| 爬虫 | `backend/scrapers/*.py` |
| 工具函数 | `backend/utils/*.py` |
| 测试 | `backend/tests/unit/`, `backend/tests/integration/` |
| 前端路由 | `web/src/routes/index.jsx` |
| 前端入口 | `web/src/App.jsx` |
| Docker | `docker-compose.yml`, `backend/Dockerfile`, `web/Dockerfile` |
| 环境配置 | `.env.example` |

### 清理目标文件清单

**重复服务文件（保留 *_typed 版本）**:
- `backend/services/auth_service.py` → 删除
- `backend/services/trending_service.py` → 删除
- `backend/services/mock_data.py` → 删除

**废弃文件**:
- `backend/api/routes.py` → 删除
- `backend/api/routes_new.py` → 删除
- `backend/api/data_import_fixed.py` → 删除
- `backend/api/trending.py.bak` → 删除
- `backend/main_full.py` → 删除
- `backend/main_simple.py` → 删除
- `backend/simple_backend.py` → 删除

**待清理的 sys.path.insert 文件**（共 40+ 处）:
- 全部 `backend/api/*.py`
- 全部 `backend/services/*.py`
- 全部 `backend/core/*.py`
- 全部 `backend/scrapers/*.py`
- 全部 `backend/repository/*.py`
- 全部 `backend/tests/**/*.py`
