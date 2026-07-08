# MediaPilot 项目文档

## 项目信息

- **项目名称**: MediaPilot v3
- **项目路径**: `C:\Users\19802\Desktop\ClaudeCodeTest\MediaPilot`
- **当前版本**: v3（重构版本）
- **项目状态**: 开发中 - Phase 1

## 产品定位

新媒体人一站式提效工具——从发现热点到创作内容，全流程自动化。

**核心工作流**:
```
发现热点 → 生成文案/脚本 → 制作视频 → 发布内容
```

---

## Phase 1 开发计划

### 总览

- **周期**: 2周
- **任务数**: 63个
- **总工时**: 189小时

### 需求列表

| # | 需求 | 优先级 | 任务数 | 状态 |
|---|------|--------|--------|------|
| 1 | 全网热点搜索 | P0 | 15 | ✅已完成 |
| 2 | 话题订阅与自动推送 | P1 | 14 | ✅已完成 |
| 3 | 口播文案生成优化 | P0 | 12 | ✅已完成 |
| 4 | 拍摄脚本生成 | P0 | 11 | ✅已完成 |
| 5 | 内容关联与追踪 | P1 | 11 | ✅已完成 |

---

## Phase 2 开发计划（待开始）

### 总览

- **周期**: 2周
- **任务数**: 43个
- **总工时**: 140小时

### 需求列表

| # | 需求 | 优先级 | 任务数 | 状态 |
|---|------|--------|--------|------|
| 6 | 音视频转写 | P1 | 14 | ✅已完成 |
| 7 | 数字人视频生成 | P2 | 14 | 待开始 |
| 8 | 视频剪辑 | P2 | 15 | 待开始 |

---

## 已完成任务：需求 2 - 话题订阅与自动推送 ✅

### 功能说明

用户订阅感兴趣的话题，系统按频率（每日 / 每 3 天）定时扫描全网热点，把新热点作为推送记录入库，用户在订阅页查看未读推送。

三件事：

1. **订阅管理** — 创建/更新/暂停/恢复/删除订阅，按用户隔离
2. **推送记录** — 调度器为到期订阅创建推送记录，用户查看/标记已读
3. **调度器** — 每日 08:00 扫描到期订阅（`next_push_at <= now`），调热点搜索，写推送记录，推进下次推送时间

### 端点

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/api/v1/subscriptions` | 订阅列表 |
| POST | `/api/v1/subscriptions` | 创建（扣配额、拒绝重复话题） |
| PUT | `/api/v1/subscriptions/{id}` | 更新（话题/描述/频率/状态） |
| DELETE | `/api/v1/subscriptions/{id}` | 删除 |
| POST | `/api/v1/subscriptions/{id}/pause` | 暂停 |
| POST | `/api/v1/subscriptions/{id}/resume` | 恢复 |
| GET | `/api/v1/subscriptions/push/records` | 推送记录（支持 unread_only） |
| POST | `/api/v1/subscriptions/push/records/{id}/read` | 标记已读 |
| GET | `/api/v1/subscriptions/push/unread-count` | 未读数 |
| GET | `/api/v1/subscriptions/health` | 健康检查 |

### 任务清单

| ID | 任务 | 负责人 | 状态 |
|----|------|--------|------|
| BE-029 | 设计订阅数据模型（SubscriptionTable + PushRecordTable） | 后端 | ✅已完成 |
| BE-030 | 实现订阅 CRUD API | 后端 | ✅已完成 |
| BE-031 | 实现暂停/恢复 API | 后端 | ✅已完成 |
| BE-032 | 实现推送记录读取/标记已读 API | 后端 | ✅已完成 |
| BE-033 | 实现调度器（定时扫描到期订阅 + 推送） | 后端 | ✅已完成 |
| BE-034 | 推送时调热点搜索服务（复用需求 1） | 后端 | ✅已完成 |
| BE-035 | next_push_at 自动推进（按频率） | 后端 | ✅已完成 |
| FE-022 | 设计订阅页面 | 前端 | ✅已完成 |
| FE-023 | 实现订阅 CRUD 交互 | 前端 | ✅已完成 |
| FE-024 | 实现推送记录展示（未读数 badge） | 前端 | ✅已完成 |
| FE-025 | 热点搜索页"前往订阅"跳转 | 前端 | ✅已完成 |
| FE-026 | 订阅页"使用此内容生成口播文案"反向跳转 | 前端 | ✅已完成 |
| QA-015 | e2e 测试（订阅完整流程 + 推送调度） | 测试 | ✅已完成 |
| QA-016 | 用户隔离测试（A 看不到 B 的订阅/推送） | 测试 | ✅已完成 |

### 测试覆盖

`backend/tests/e2e/test_subscription_flow.py` — 22 tests，覆盖：
- 订阅 CRUD + 配额扣减 + 重复话题拒绝 + 用户隔离
- 暂停/恢复 + 默认列表不显示暂停项
- 推送记录读取 + 标记已读 + 未读数 + unread_only 筛选
- 调度器：到期订阅触发推送、推进 next_push_at；无热点不崩溃；未到期不推送

### 过程中修复的 Bug

1. **DELETE/pause/resume/mark_read 找不到时返 400 而非 404**：服务层抛 `ValueError("订阅不存在")`，API 笼统映射成 400。修复：抽 `_map_value_error` 按 message 文案区分 404（"不存在"）/ 403（"无权"）/ 400
2. **`PersonaRepository` 同微秒排序失败**：测试在 1 微秒内连续 create+update，`last_used_at` 全相等，无法区分"最近用过"。之前用 `desc(id)` 反而让最新创建的排前面（语义错）。修复：回滚 `desc(id)`，测试加 `time.sleep(0.01)` 推进时间——这是测试环境的人为快速操作问题，不是产品 bug

---

## 已完成任务：需求 5 - 内容关联与追踪 ✅

### 功能说明

把"散落的内容"用「热点」这条主线串起来，让需求 1/3/4 的产出可追溯、可复盘。

三件事：

1. **内容库** — 文案/脚本生成时自动登记入库（user_id / content_type / hot_topic_id / is_processed）
2. **热点→内容反查** — 给一条 hot_topic_id，返回它催生的所有文案和脚本
3. **话题趋势历史** — 每条热点按时间累积热度记录，可看曲线判断涨跌

### 端点

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/api/v1/content-library/contents` | 内容列表（筛选 type/processed/hot_topic） |
| POST | `/api/v1/content-library/contents` | 显式创建（一般由生成端点自动调） |
| GET | `/api/v1/content-library/contents/{id}` | 详情 |
| PUT | `/api/v1/content-library/contents/{id}` | 更新 |
| DELETE | `/api/v1/content-library/contents/{id}` | 删除 |
| POST | `/api/v1/content-library/contents/{id}/process` | 标记已用 |
| GET | `/api/v1/content-library/hot-topic/{hot_topic_id}/contents` | 热点反查 |
| POST | `/api/v1/content-library/topic-history` | 话题历史趋势 |
| GET | `/api/v1/content-library/health` | 健康检查 |

### 任务清单

| ID | 任务 | 负责人 | 状态 |
|----|------|--------|------|
| BE-023 | 设计内容库数据模型（ContentTable + HotTopicTrendTable） | 后端 | ✅已完成 |
| BE-024 | 实现内容库 CRUD API | 后端 | ✅已完成 |
| BE-025 | 实现热点反查 API（hot_topic_id → contents） | 后端 | ✅已完成 |
| BE-026 | 实现话题趋势历史 API | 后端 | ✅已完成 |
| BE-027 | 文案/脚本生成时自动入库（关联热点 ID） | 后端 | ✅已完成 |
| BE-028 | 用户隔离（不同用户看不到对方内容） | 后端 | ✅已完成 |
| FE-019 | 设计内容库页面 | 前端 | ✅已完成 |
| FE-020 | 实现内容列表 + 筛选 | 前端 | ✅已完成 |
| FE-021 | 实现话题历史趋势页 | 前端 | ✅已完成 |
| QA-013 | 单元测试（仓库层） | 测试 | ✅已完成 |
| QA-014 | e2e 测试（完整流程 + 跨需求集成） | 测试 | ✅已完成 |

### 测试覆盖

- `backend/tests/unit/test_content_tracking.py` — 23 tests，覆盖 ContentLibraryRepository 和 HotTopicTrendRepository 全部方法
- `backend/tests/e2e/test_content_library_flow.py` — 22 tests，覆盖 9 端点 + 用户隔离 + 跨需求集成（copywriting/shoot_script 入库后能反查到）

### 过程中修复的 Bug

1. **`ensure_dev_user` 导致用户隔离失效**：content_library 8 个端点用 `ensure_dev_user(db)` → 永远返回同一个 dev user（username="dev"），所有用户共享一个内容库。修复：全部改为 `Depends(get_current_user)`，按 JWT 用户隔离
2. **DELETE / process 找不到内容时返 400 而非 404**：服务层抛 `ValueError("内容不存在")`，API 笼统映射成 400 INVALID_INPUT。修复：API 检查 message 区分"不存在"→404、"无权"→403、其余→400
3. **PersonaRepository 同秒排序不确定**：SQLite datetime 默认秒级精度，4 个操作同秒完成时 `last_used_at` 全相等，排序靠 id 兜底，LRU 顺序错乱。修复：`order_by` 加 `desc(id)` 二级排序
4. **测试债**：`test_content_tracking.py` 三处脱节——import 路径错（`content_repo` → `content_library_repo`）、参数名错（`content_id=` → `content_uuid=`）、方法名不存在（`get_by_topic_id` → `get_topic_trends`）

---

## 已完成任务：需求 4 - 拍摄脚本生成 ✅

### 功能说明

生成视频拍摄脚本，支持三平台 × 三风格矩阵：

- **平台**：抖音（60s 竖屏 5 镜头）/ 小红书（3min 竖屏 8 镜头）/ B 站（5-10min 横屏 15 镜头）
- **风格**：energetic 激情热血 / relaxed 轻松幽默 / professional 专业分析
- **输出**：标题 + 钩子 + 分镜头脚本（编号/时长/画面/台词/场景/运镜）+ 行动号召 + 标签

### 端点

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/api/v1/shoot-script/generate` | 生成拍摄脚本 |
| GET | `/api/v1/shoot-script/{script_id}` | 获取已生成脚本 |
| POST | `/api/v1/shoot-script/export` | 导出（json/txt/csv） |
| GET | `/api/v1/shoot-script/health` | 健康检查 |

### 任务清单

| ID | 任务 | 负责人 | 状态 |
|----|------|--------|------|
| FE-015 | 设计拍摄脚本生成页面 | 前端 | ✅已完成 |
| FE-016 | 实现平台/风格选择组件 | 前端 | ✅已完成 |
| FE-017 | 实现分镜头展示与导出 | 前端 | ✅已完成 |
| FE-018 | 与内容库关联保存 | 前端 | ✅已完成 |
| BE-019 | 设计拍摄脚本数据模型 | 后端 | ✅已完成 |
| BE-020 | 实现脚本生成 API（三平台三风格） | 后端 | ✅已完成 |
| BE-021 | 实现脚本导出 API（json/txt/csv） | 后端 | ✅已完成 |
| BE-022 | 脚本与内容库关联 | 后端 | ✅已完成 |
| QA-010 | 单元测试（脚本生成逻辑） | 测试 | ✅已完成 |
| QA-011 | 集成测试（脚本生成 API） | 测试 | ✅已完成 |
| QA-012 | 端到端测试（完整脚本生成流程） | 测试 | ✅已完成 |

### 测试覆盖

- `backend/tests/unit/test_shoot_script_service.py` — 24 tests，覆盖 `_get_platform_config` / `_build_prompt` / `_mock_generate` / `_parse_ai_result` / `_calculate_duration`
- `backend/tests/e2e/test_shoot_script_flow.py` — 24 tests，覆盖三平台×三风格生成、按 ID 查询、三格式导出、配额扣减、健康检查

### 过程中修复的 Bug

1. **路由顺序错误**：`/health` 定义在 `/{script_id}` 之后被吞掉 → 404。修复：`/health` 上移至首位
2. **`_parse_ai_result` 镜头号解析 bug**：`"".join([c for c in line if c.isdigit()])` 会把 `镜头1 [时长：0:00-0:08]` 中的 `1000008` 当作 shot_number。修复：只取"镜头"后连续数字段；并兼容内联 `[时长：x:xx]`
3. **`Shot` 缺 `duration` 时响应 400**：AI 输出未含时长字段导致 `ShootScriptResponse` 校验失败。修复：在解析收尾处 `_flush()` 补默认 `duration` / `visual_description`
4. **JSON 导出 `datetime` 序列化崩溃**：`json.dumps(model_dump())` 不处理 datetime。修复：改用 `model_dump_json(indent=2)`
5. **`/generate` 误用 `ensure_dev_user`**：扣的是 dev user 的配额而非 JWT 用户的，与 copywriting 不一致。修复：改用 `get_current_user` 依赖

---

## 已完成任务：需求 3 - 口播文案生成 ✅

### 功能说明

生成口播文案，支持三种模式：
1. **从0到1**：用户输入话题 + 人设 → 生成口播文案
2. **热点框架**：热点介绍/总结 + 人设 → 生成口播文案
3. **改写**：复制文案 + 人设 → 洗稿重写

### 功能特性

- **人设系统**：存储用户最近3次输入的人设用于快捷选取
- **再改改功能**：点击选项 - 更口语化、加情绪、加观点
- **输出格式**：标题 + 钩子 + 文案（工整格式）

### 任务清单

| ID | 任务 | 负责人 | 状态 |
|----|------|--------|------|
| FE-010 | 设计口播文案生成页面 | 前端 | ✅已完成 |
| FE-011 | 实现人设输入组件（含快捷选取） | 前端 | ✅已完成 |
| FE-012 | 实现三种模式切换 | 前端 | ✅已完成 |
| FE-013 | 实现"再改改"功能 | 前端 | ✅已完成 |
| FE-014 | 在热点搜索添加跳转提示 | 前端 | ✅已完成 |
| BE-015 | 设计人设存储数据模型 | 后端 | ✅已完成 |
| BE-016 | 实现口播文案生成 API | 后端 | ✅已完成 |
| BE-017 | 实现文案改写 API | 后端 | ✅已完成 |
| BE-018 | 实现AI文案参考爬虫（微博/百度/知乎） | 后端 | ✅已完成 |
| QA-007 | 单元测试（文案生成逻辑） | 测试 | ✅已完成 |
| QA-008 | 集成测试（文案生成 API） | 测试 | ✅已完成 |
| QA-009 | 端到端测试（完整文案生成流程） | 测试 | ✅已完成 |

---

## 需求 1 - 全网热点搜索 ✅

### 功能说明

按关键词搜索全网热点新闻，支持时间范围筛选，返回 10 条热点，每条带摘要、热度指标和趋势方向。数据源：百度新闻、微博热搜、知乎热榜、抖音热榜、小红书等，使用网页抓取不依赖付费 API。

### 任务清单

| ID | 任务 | 负责人 | 状态 |
|----|------|--------|------|
| FE-001 | 设计新的热点搜索页面 | 前端 | ✅已完成 |
| FE-002 | 实现热点列表展示组件 | 前端 | ✅已完成 |
| FE-003 | 实现时间范围选择器 | 前端 | ✅已完成 |
| FE-004 | 实现热度指标和趋势展示 | 前端 | ✅已完成 |
| BE-001 | 设计热点数据结构 | 后端 | ✅已完成 |
| BE-002 | 实现百度新闻搜索爬虫 | 后端 | ✅已完成 |
| BE-003 | 实现微博热搜爬虫 | 后端 | ✅已完成 |
| BE-004 | 实现知乎热榜爬虫 | 后端 | ✅已完成 |
| BE-005 | 实现抖音热榜爬虫 | 后端 | ✅已完成 |
| BE-006 | 实现小红书趋势爬虫 | 后端 | ✅已完成 |
| BE-007 | 实现数据聚合与去重逻辑 | 后端 | ✅已完成 |
| BE-008 | 实现热点搜索API (POST /api/v1/trending/search) | 后端 | ✅已完成 |
| QA-001 | 单元测试（爬虫解析逻辑） | 测试 | ✅已完成 |
| QA-002 | 集成测试（搜索 API） | 测试 | ✅已完成 |
| QA-003 | 端到端测试（完整搜索流程） | 测试 | ✅已完成 |

---

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | React 19 + Vite + Tailwind CSS |
| 后端 | FastAPI + SQLAlchemy + Pydantic v2 |
| AI | 火山引擎 Ark API |
| 数字人 | 火山引擎 API |
| 语音转写 | Whisper 本地 / 火山引擎 |
| 视频剪辑 | FFmpeg |
| 热点搜索 | 网页抓取（百度新闻、微博、知乎等） |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） |
| 认证 | JWT（access_token + refresh_token） |

---

## 项目路径

- 后端: `backend/`
- 前端: `web/src/`
- 数据库: `mediapilot.db`

---

## 端口配置

**统一端口规范，严禁修改**：

| 服务 | 端口 | 配置位置 |
|------|------|----------|
| 前端开发服务器 | 5173 | `web/vite.config.ts` |
| 后端 API 服务 | 8000 | `backend/main.py` |
| 前端代理目标 | 8000 | `web/vite.config.ts` |

**测试链接**：
- 前端热点搜索: `http://localhost:5173/trending`
- 后端 API: `http://localhost:8000/api/v1/`

---

## 更新日志

### 2026-07-08
- 清 v3 测试老债：12 个 fail → 0（全量 455 passed / 4 skip，另有 1 个 live-AI flaky 见下）
- P0 真 bug 修复：`copywriting_service.get_copywriting` 缺 `def` 函数头的孤儿代码补全 —— 前端「再改改」改写此前直接 500，现恢复
- 删死代码：`platform_api._fetch_{weibo,douyin,xiaohongshu}_trending` + `_mock_hot_topics`（v2 遗留，全项目无调用），连带删/重写测死代码的用例。原则：没有真实数据源就如实 degraded 降级，绝不用 mock 假数据冒充
- `test_platform_api` 重写：mock scraper 网络边界（合法 I/O 打桩），验证真实聚合/排序/降级契约，含「无数据源→topics 为空、进 degraded_platforms」用例固化原则
- `test_trending_service` 修正：断言从不存在的 `platform`/`trend` 字段 → 真实契约 `source`/`heat_value`/`trend_direction`；mock 掉网络保证确定性
- `test_calendar_service` 修复：`create_event` 测试补 `db.flush()` 回填 id/created_at 的打桩（原 mock_event 是摆设，未被 service 使用）
- 测试基建修复：`conftest.db_setup` 把 `media_service.SessionLocal` 重定向到测试内存引擎 —— 后台异步任务此前自建 session 写向生产库，导致 TestClient 内存库永远读不到任务结果；media 集成测试改轮询后现可确定性完成
- ⚠️ 遗留 flaky：`test_copywriting_flow.py::test_rewrite_each_direction[more_colloquial]` 依赖真实 AI 返回可解析非空 content，偶发空返回致断言失败（复跑即过）。非本次改动引入，待决定是否 mock AI 固定化
- ⚠️ 待清理：`CompetitorAPI` / `_mock_competitors`（对标账号）功能已在 2026-05-14 标记清理，但类+mock+测试仍在，属同类死 mock 债

### 2026-06-20
- 完成需求 6：音视频转写（前端接入真实 `/api/v1/media/upload` + 轮询 `/media/task/{id}`，替换 mock）
- 新增前端服务 `web/src/services/media.js`（uploadMedia / getMediaTask / pollMediaTask）
- 重构 `use-transcription.js`：file 模式从 simulateTranscription 切到真实 API 轮询，realtime 模式保留浏览器 SpeechRecognition
- `TranscriptionPage.jsx` 增加时间戳/大纲/任务错误展示
- 新增 e2e 测试 `test_media_flow.py`（7 cases，含配额扣减、404、未授权 401）
- 完成需求 2：话题订阅与自动推送（BE-029~035 / FE-022~026 / QA-015~016 全部 ✅）
- 新增 e2e 测试 `test_subscription_flow.py`（22 cases，含调度器集成）
- 修复 2 个 bug：subscription 4 端点返 400 应为 404/403、PersonaRepository 同微秒排序失败
- 完成需求 5：内容关联与追踪（BE-023~028 / FE-019~021 / QA-013~014 全部 ✅）
- 新增 e2e 测试 `test_content_library_flow.py`（22 cases，含跨需求集成）
- 修复 4 个 bug：content_library 用户隔离失效、DELETE/process 返 400 应为 404、PersonaRepository 同秒排序不确定、test_content_tracking 三处测试债
- 完成需求 4：拍摄脚本生成（FE-015~018 / BE-019~022 / QA-010~012 全部 ✅）
- 新增 e2e 测试 `test_shoot_script_flow.py`（24 cases）和单元测试 `test_shoot_script_service.py`（24 cases）
- 修复 5 个 bug：路由顺序、镜头号解析、Shot 缺 duration、JSON 导出 datetime、`/generate` 用错用户

### 2026-05-14
- 开始需求3：口播文案生成
- 清理过时功能（对标账号、发布日历、数据导入）
- 添加AI内容格式规范

### 2026-05-13
- 创建项目 CLAUDE.md
- 记录 Phase 1 和 Phase 2 开发计划
- 开始 Phase 1 开发

---

## 数据真实性原则（重要）

**不用 mock 假数据冒充做不了的功能。** 没有真实数据源 / 服务不可用时，必须如实降级
（degraded / 报错 / 返回空），让用户明确知道「这个源暂时没有」，绝不用模板拼的假数据糊弄。

- 热点搜索：平台无可用 scraper → 标 `degraded_platforms`，前端黄条提示，topics 不塞假数据
- 文案生成：AI 不可用 → 抛错，不回退「X运营技巧」这类模板 mock（污染用户内容）
- 测试里 mock 只用于**打桩 I/O 边界**（网络 / DB / 外部 API）以获得确定性，
  不用于伪造产品功能。测「无数据源」时应断言「如实降级」，而非「返回 mock」

## AI 内容格式规范

**所有AI生成的内容必须遵守以下规范：**

1. **禁止使用"#"符号**：AI生成的文案、标题、钩子中不得出现任何"#"字符
2. **格式必须工整**：标题、钩子、文案之间要有清晰的分隔和格式
3. **输出格式**：标题 + 钩子（2-3个备选）+ 文案主体
4. **去除AI感**：避免使用"本文""文章""综上所述"等AI常用表达

---

## 开发协作方式

开发过程中调用 MCP 工具：
- `dev.fe.*` - 前端工程师工具
- `dev.be.*` - 后端工程师工具
- `dev.qa.*` - 测试工程师工具
- `dev.pm.*` - 项目主管工具
