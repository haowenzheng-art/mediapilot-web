# MediaPilot v3 发布检查清单

## 后端

### 配置 & 环境
- [ ] `.env` 含 `AI_API_KEY` / `AI_BASE_URL` / `AI_MODEL`（火山引擎 Ark）
- [ ] `DATABASE_URL` 指向 PostgreSQL（生产）或 SQLite（开发）
- [ ] `REDIS_URL` 可达，worker 能注册
- [ ] `JWT_SECRET_KEY` ≥ 32 字符随机
- [ ] `DEV_MODE=false` 禁用 dev-user 注入
- [ ] `RATE_LIMIT_ENABLED=true` 开启限流
- [ ] `SENTRY_DSN` 可选；填了则自动接入
- [ ] `LOG_RETENTION_DAYS=7`（按日轮转）

### 数据库
- [ ] `alembic upgrade head` 在生产成功执行（含 preferences / calendar_events 两条新迁移）
- [ ] 备份策略：每日全量 + WAL 增量

### 关键端点烟测
- [ ] `GET /health` → 200
- [ ] `GET /queue/health` → status:ok, redis:connected, registered_functions 含 transcribe_audio_file 等
- [ ] `POST /api/v1/auth/register` → 注册 + token
- [ ] `POST /api/v1/trending/search`（带 token）→ 含 hot_topics，含 `is_today` 字段
- [ ] `POST /api/v1/copywriting/generate`（三模式）
- [ ] `POST /api/v1/shoot-script/generate`（三平台×三风格）
- [ ] `GET /api/v1/preferences` / `PUT /api/v1/preferences`
- [ ] `GET /api/v1/analytics/dashboard?days=30`
- [ ] `GET/POST /api/v1/calendar/events`
- [ ] `POST /api/v1/competitors/search` → 含 `is_demo`
- [ ] `POST /api/v1/ai/tutor` 关键词命中 / 兜底两条路径

### 自动化
- [ ] `pytest backend/tests/e2e/ -q` 全绿（≥132 通过）
- [ ] AI Circuit breaker：连续 5 次失败进入冷却（30s）
- [ ] Agent max_iterations 硬上限 10 不可突破

## 前端
- [ ] 构建 `pnpm build` 通过，无 console error
- [ ] `/trending` 显示 `today` 徽章（is_today=true）
- [ ] `/competitors` 显示 `demo` 徽章（is_demo=true）
- [ ] `/settings` 主题/语言切换持久化（服务端 + localStorage）
- [ ] `/analytics` 显示真实数据，零内容时显示空态
- [ ] `/calendar` 创建/编辑/删除事件，状态变更
- [ ] AI Chat 调用 `/ai/tutor` 时显示跳转按钮

## 监控 & 回滚
- [ ] Sentry 收到一条 test event
- [ ] Grafana / 日志面板能看到 `req_id` 贯通的访问日志
- [ ] 回滚预案：上一稳定标签 + DB 备份恢复脚本路径

## 已知限制
- 真实平台 API（灰豚/新榜/微博热搜）未接入，对标账号默认 demo 数据
- Whisper 转写为本地推理，长视频耗时；线上可配 `USE_VOLCENGINE_ASR=true` 走火山 ASR
