# MediaPilot 代码规范

## 一、模块拆分原则（职责单一）

### 1.1 职责单一原则 (SRP)

每个模块只负责一个明确的功能领域：

- **api/**: 仅处理 HTTP 请求/响应，不包含业务逻辑
- **services/**: 核心业务逻辑，可被多个入口调用
- **repository/**: 数据库 CRUD 操作，不包含业务规则
- **models/**: 数据结构定义，无逻辑处理
- **core/**: 外部系统交互（AI、第三方API等）
- **utils/**: 纯工具函数，无状态，可测试

### 1.2 依赖方向

```
api → services → repository → models
        ↓
     core
```

禁止反向依赖：
- ❌ service 不能调用 api
- ❌ repository 不能调用 service
- ❌ model 不能调用任何业务层

### 1.3 层级边界

| 层级 | 能做的事情 | 不能做的事情 |
|------|------|---------|------|
| API | 参数校验、调用 Service、格式化响应 | 直接操作数据库、包含业务逻辑 |
| Service | 组合业务逻辑、调用 Repository、调用 Core Service | 处理 HTTP、直接访问数据库 |
| Repository | 数据库 CRUD 操作 | 业务判断、格式化数据 |
| Model | | 任何逻辑处理 |

---

## 二、命名规范

### 2.1 文件命名

#### Python (后端)

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写，下划线分隔 | `trending_service.py` |
| 类模块 | 小写，下划线分隔 | `hot_topic.py` |
| 测试文件 | `test_` + 模块名 | `test_trending_service.py` |

#### JavaScript/React (前端)

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件文件 | PascalCase | `ScriptPage.jsx` |
| 工具文件 | 小写，连字符/下划线 | `use-theme.js` |
| 样式文件 | 小写，连字符 | `global.css` |

### 2.2 变量命名

#### Python

```python
# 常量：大写下划线
MAX_RETRY_COUNT = 3
API_TIMEOUT = 30

# 变量/函数：小写下划线
def search_trending(keyword: str) -> List[HotTopic]:
    pass

# 类：PascalCase
class HotTopic:
    pass

# 私有属性：前缀下划线
self._internal_data
```

#### JavaScript

```javascript
// 常量：大写下划线
const MAX_RETRY = 3

// 变量/函数：小驼峰
function searchTrending(keyword) {}

// 组件：PascalCase
function ScriptPage() {}

// 私有变量：前缀下划线
let _internalData
```

### 2.3 文件夹命名

- 全部小写，使用连字符或下划线
- 后端推荐下划线：`trending_service/`
- 前端推荐连字符：`use-theme/`

---

## 三、模块间引用规范

### 3.1 入口文件暴露原则

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

### 3.2 引用规范

```python
# 推荐：通过入口文件引用
from services import TrendingService

# 避免：直接引用内部模块
from services.trending_service import TrendingService
```

### 3.3 循环引用检测

如果出现循环引用：
1. 检查是否违反依赖方向原则
2. 将共享部分抽取到独立模块
3. 使用依赖注入解耦

---

## 四、代码风格与注释要求

### 4.1 Python 遵循 PEP 8

使用 `black` 格式化：
```bash
pip install black
black backend/
```

### 4.2 JavaScript 使用 ESLint + Prettier

```json
{
  "extends": ["eslint:recommended", "prettier"],
  "rules": {
    "semi": ["error", "always"],
    "quotes": ["single"]
  }
}
```

### 4.3 注释规范

#### 文件头部注释

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

#### 函数注释

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

### 4.4 禁止事项

- ❌ 禁止无意义的注释（如 `i += 1  # 加1`）
- ❌ 禁止注释掉的代码（使用 Git 管理）
- ❌ 禁止行内注释影响代码可读性
- ❌ 禁止魔法数字，使用常量替代

---

## 五、Git 提交规范

使用 Conventional Commits 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| 类型 | 说明 |
|------|------|
| feat | 新功能 |
| fix | 修复bug |
| refactor | 重构代码 |
| docs | 文档变更 |
| style | 代码格式调整 |
| test | 测试相关 |
| chore | 构建/工具相关 |

### 示例

```bash
git commit -m "feat(services): 添加热点搜索业务逻辑

- 从 mock_data 提取搜索逻辑
- 封装到 TrendingService 类
- 提取入参数校验

Closes #123"
```

---

## 六、测试规范

### 6.1 测试文件结构

```
backend/
├── tests/
│   ├── unit/
│   │   └── test_trending_service.py
│   └── integration/
│   │   └── test_api_trending.py
```

### 6.2 测试命名

```
def test_功能_场景_预期():
    pass
```

### 6.3 测试覆盖

- 核心 Service 层单元测试覆盖率 > 80%
- API 层集成测试覆盖所有端点
- 边界组件测试关键用户路径

---

## 七、配置管理

### 7.1 环境变量

使用 `.env` 文件，不提交到 Git：

```bash
# .env
API_KEY=sk-xxx
DATABASE_URL=sqlite:///./mediapilot.db
AI_MODEL=claude-3-opus-20240229
```

### 7.2 敏感信息

绝对禁止：
- ❌ 代码中硬编码 API Key
- ❌ 提交 `.env` 文件
- ❌ 日志输出敏感（密码、token、个人信息）

### 7.3 配置类

- 使用 `pydantic-settings` 管理配置：
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_key: str = Field(default="", description="API Key")
    database_url: str = Field(default="sqlite:///./mediapilot.db")
```

---

## 八、持续检查

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

## 九、架构演进最佳实践（从 Phase 1-3 重构总结）

### 9.1 三层架构模式

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

### 9.2 模块间引用规范

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

### 9.3 路由由模块化

**单个路由文件模板**
```python
"""
功能描述路由
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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

### 9.4 环境变量配置

- 使用 `pydantic-settings` 管理配置
- 配置类统一放在 `backend/config/settings.py`
- 通过 `from config.settings import settings` 导入
- 环境变量读取：`os.getenv("KEY", default_value)`

### 9.5 迁移兼容策略

从单体结构迁移到分层结构时：
1. 先创建新结构文件
2. 保留旧文件作为 fallback
3. 使用 try-except 导入保证向后兼容
4. 验证新结构工作后再删除旧文件
