# 更新日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 规范。

---

## [v3.0.0] - 2026-06-26（开发中）

### 新增
- **产品故事 + Hero 截图**：README 与 PRD 顶部加入"AI 时代营销能力"叙事，引用 `docs/screenshots/home.png` Hero 首页截图

### 变更
- **内容库 / 话题订阅页对齐设计系统**：移除 Tailwind 渐变和双重 padding，改用 `PageContainer` + CSS vars（`--card-bg` / `--border-color` / `--text-primary`），与热点搜索 / 口播文案 / 拍摄脚本页视觉统一
- **`ContentCard` 重写**：inline style + CSS vars，hover 用 `var(--accent-primary)` 边框，去掉 `bg-purple-100` / `text-purple-700` 等紫色硬编码
- **订阅页弹窗**：改用与登录弹窗一致的 `Modal` 组件（`backdrop-filter: blur` + `var(--bg-primary)` 背景）

### 移除
- **AI 模板功能下线**：无后端 API、与口播文案功能重叠、不在 PRD 9 个需求内。删除 `TemplatesPage` / `use-templates` hook / `ROUTE_PATHS.TEMPLATES` / `HISTORY_TYPES.TEMPLATE` / Tabs 入口 / ContentPage 路由
- **全网热点搜索**：百度/微博/知乎/抖音/小红书五端聚合，`is_today` 今日徽章，AI 总结，CSV 导出
- **话题订阅与自动推送**：订阅话题，每日 08:00 APScheduler 自动扫描新热点推送，未读数 badge，用户隔离
- **口播文案生成**：从0到1 / 热点框架 / 改写三模式，人设系统，"再改改"（更口语化/加情绪/加观点）
- **拍摄脚本生成**：三平台（抖音/小红书/B站）× 三风格矩阵，分镜头脚本，json/txt/csv 导出
- **内容关联与追踪**：文案/脚本自动入库，热点反查，话题趋势曲线
- **音视频转写**：Whisper 本地转写，时间轴 + 大纲，异步任务轮询
- **视频分析**：B站视频信息解析 + 逐字稿提取
- **AI 产品导师**：YAML 知识库（11 FAQ）+ 关键词匹配 + LLM 兜底
- **数据看板**：真实用户活动数据，`/api/v1/analytics/dashboard`
- **发布日历**：`/api/v1/calendar/events` CRUD
- **偏好设置**：主题/语言/默认平台，服务端 + localStorage 持久化
- **对标账号**：`is_demo` 徽章，无 API key 时返回 mock 数据
- **限流中间件**：按端点配置 rate limit
- **请求链路追踪**：`req_id` 贯通访问日志
- **Sentry 异常上报**：可选接入
- **v3 发布检查清单**：`docs/release/v3-launch-checklist.md`

### 修复
- **智能转写完成延迟**：Whisper 转写完成后不再被 AI 大纲生成阻塞（100s → 立即返回）
- **登录跨域失败**：前端登录服务硬编码 `http://localhost:8000` 改为同源代理 `/api/v1/auth`
- **competitors_router 未挂载**：补挂 `/api/v1/competitors/*`
- **ai_chat_router 未挂载**：补挂 `/api/v1/ai/tutor`
- **`export_competitors` 方法缺失**：补齐 import_export_service 方法
- **中文文件名下载乱码**：Content-Disposition RFC 5987 编码
- **`is_today` 字段未计算**：HotTopicResponse 加 `@model_validator`
- **视频分析静默回退 mock**：非 B站平台改为 422 明确报错
- **subscription/content_library 4 端点返 400 应为 404/403**：区分"不存在"/"无权"/"参数错误"
- **PersonaRepository 同微秒排序失败**：测试加 `time.sleep(0.01)` 推进时间
- **拍摄脚本路由顺序**：`/health` 被 `/{id}` 吞掉
- **镜头号解析 bug**：`"".join(digits)` 把 `1000008` 当 shot_number
- **Shot 缺 duration**：AI 输出未含时长时补默认值
- **JSON 导出 datetime 序列化崩溃**：改用 `model_dump_json`
- **`/generate` 误用 dev_user**：扣错配额，改用 JWT 用户

### 变更
- 视频分析支持范围收敛为 **仅 B站中文视频**，其他平台入口下线
- 智能转写流程：转写完成立即返回 transcript + 默认大纲，AI 大纲不再阻塞
- 前端平台选择器从 4 平台收敛为 B站

### 移除
- 旧版主题切换（ThemeSwitcher / ThemeContext / use-theme）
- 旧版背景组件（AbstractBackground / AnimeBackground / CyberpunkBackground 等）
- 旧版独立页面（AnalyticsPage / CalendarPage / CompetitorsPage 等旧实现）

---

## [v2.0.0-alpha.2] - 2026-06

### 新增
- Agent 架构完整跑通：agnes-2.0-flash 模型
- backend + worker + redis 三服务联调 OK
- Tool 注册：search_hotspots / generate_copywriting / get_content_library

---

## [v2.0.0-alpha] - 2026-06

### 新增
- 企业级重构：工程基座 + 异步体系 + Agent 架构
- ARQ 异步任务队列（Redis 后端）
- APScheduler 定时调度
- JWT access + refresh token 认证
- 配额体系（扣减 / 退还 / 检查）
- Pydantic v2 schema
- Alembic 数据库迁移
- 分层架构：api / services / repositories / models

---

## [v1.0.0] - 2026-03

### 新增
- 基础热点追踪
- 对标账号分析（小红书/抖音，Excel 导出）
- 爆款视频分析（逐字稿 + 改写）
- 音视频转写
- 内容生成（分镜头脚本 + 文案）
- 数据看板
- 内容日历
- AI 助手（多模型支持）
- Windows 桌面端（PyQt5）

---

[未发布]: https://github.com/haowenzheng-art/mediapilot-web/compare/v1.0.0...HEAD
