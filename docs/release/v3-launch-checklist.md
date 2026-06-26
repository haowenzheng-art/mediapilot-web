# MediaPilot v3 发布检查清单

> 适用版本：v3.0.0（Phase 1 完成）
> 当前 v3 前端 sidebar 暴露 7 个页面：trending / copywriting / shoot-script / subscription / content-library / transcription / video-analysis
> 后端 17 个 router 全挂载（含未暴露 UI 的 preferences / analytics / calendar / competitors / agent）

## 后端

### 配置 & 环境
- [ ] `.env` 含 `AI_API_KEY` / `AI_BASE_URL` / `AI_MODEL`（火山引擎 Ark 或 OpenAI 兼容）
- [ ] `DATABASE_URL` 指向 PostgreSQL（生产）或 SQLite（开发）
- [ ] `REDIS_URL` 可达，worker 能注册（`/queue/health` 返回 `registered_functions` 非空）
- [ ] `JWT_SECRET` ≥ 32 字符且非占位符（当前 `.env` 默认值 `your-secret-key-change-in-production` 是占位符，**生产必须替换为强随机值**）
- [ ] `DEV_MODE=false`（settings 默认 False；本地开发需显式设 `DEV_MODE=true` 才能用 `ensure_dev_user`）
- [ ] `RATE_LIMIT_ENABLED=true`（默认 True，禁止关闭）
- [ ] `SENTRY_DSN` 可选；填了则自动接入
- [ ] `LOG_RETENTION_DAYS=7`（默认值，按日轮转）
- [ ] `CORS_ORIGINS` 生产环境显式列出（DEV_MODE=False 时不能为空）

### 数据库
- [ ] `alembic upgrade head` 在生产成功执行（当前 head: `fcf774614a16`）
- [ ] 备份策略：每日全量 + WAL 增量

### 关键端点烟测（v3 实际路由）
- [ ] `GET /health` → `status: healthy`，DB + Redis + AI + transcribe 全部 OK
- [ ] `GET /queue/health` → `status: ok`，`registered_functions` 含 `generate_copywriting_job` / `search_trending_job`（媒体转写走同步路径不进 ARQ）
- [ ] `POST /api/v1/auth/register` / `POST /api/v1/auth/login` → token + refresh_token
- [ ] `POST /api/v1/trending/search`（带 token）→ 含 `hot_topics`，含 `is_today` 字段
- [ ] `POST /api/v1/copywriting/generate`（三模式：scratch / hotspot / rewrite）
- [ ] `POST /api/v1/shoot-script/generate`（三平台 × 三风格 = 9 组合）
- [ ] `GET /api/v1/subscriptions` / `POST` 创建订阅 → 扣配额 + 拒绝重复话题
- [ ] `POST /api/v1/subscriptions/push/trigger`（admin only）→ 立即推送 + 创建 push records
- [ ] `GET /api/v1/subscriptions/push/records` → 推送记录列表
- [ ] `GET /api/v1/content-library/contents` → 内容列表
- [ ] `GET /api/v1/content-library/hot-topic/{hot_topic_id}/contents` → 热点反查
- [ ] `POST /api/v1/content-library/topic-history` → 话题趋势曲线
- [ ] `POST /api/v1/media/upload`（带 token）→ 异步转写任务
- [ ] `GET /api/v1/media/task/{id}` → 轮询任务状态
- [ ] `POST /api/v1/ai/tutor` → 关键词命中 / LLM 兜底两条路径
- [ ] `GET /api/v1/preferences` / `PUT` → 偏好持久化（后端挂载，前端未暴露入口）
- [ ] `GET /api/v1/analytics/dashboard?days=30` → 真实活动数据（后端挂载）
- [ ] `GET/POST /api/v1/calendar/events` → 事件 CRUD（后端挂载）
- [ ] `POST /api/v1/competitors/search` → `is_demo` 徽章（后端挂载）

### 自动化
- [ ] `python -m pytest backend/tests/e2e/ -q` 全绿（≥132 通过；当前基线见 `docs/reports/v2.0-stability-acceptance-2026-06-17.md`）
- [ ] AI Circuit breaker：连续 5 次失败进入冷却（30s）
- [ ] Agent max_iterations 硬上限 10 不可突破

## 前端
- [ ] `npm run build` 通过，无 console error
- [ ] `/trending` 显示 `today` 徽章（`is_today=true`）
- [ ] `/copywriting` 三模式切换正常，"再改改"按钮触发改写
- [ ] `/shoot-script` 9 组合生成 + 三格式导出（json/txt/csv）
- [ ] `/subscription` 创建订阅 → 重复话题被拒绝 → 暂停/恢复 → 推送记录列表有未读 badge
- [ ] `/content-library` 列表 + 筛选 + 详情弹窗 + 删除（无颜色对比问题，黑底白字清晰可读）
- [ ] `/transcription` 文件上传 + 轮询任务状态 + 时间轴展示
- [ ] `/video-analysis` B站视频解析 + 逐字稿（非 B站返 422）

## 监控 & 回滚
- [ ] Sentry 收到一条 test event（如配置）
- [ ] Grafana / 日志面板能看到 `req_id` 贯通的访问日志
- [ ] 回滚预案：上一稳定标签 + DB 备份恢复脚本路径
- [ ] **APSchedued 推送任务验证**：admin 调 `POST /api/v1/subscriptions/push/trigger`，确认 push records 入库且 `next_push_at` 推进

## 已知限制
- 真实平台 API（灰豚/新榜/微博热搜）未接入，对标账号默认 demo 数据
- Whisper 转写为本地推理，长视频耗时；线上可配 `USE_VOLCENGINE_ASR=true` 走火山 ASR
- 前端 sidebar 未暴露 preferences / analytics / calendar / competitors 入口，API 已挂载可被外部调用
- 数字人视频生成（需求 7）/ 视频剪辑（需求 8）属于 Phase 2，未实现
