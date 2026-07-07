# MediaPilot v3 冲刺 — 当前进度快照

**最后更新**：2026-07-07  
**main 最新 commit**：`69dfa32`（chore(test-debt): 清理 23 处 v3 测试债）

## 用户三大反馈全部交付

| 反馈 | 解决方案 | commit |
|---|---|---|
| **AI 生成响应慢** | copywriting + shoot-script SSE 流式 + reasoning 折叠区 | `b7ffbd1` `f34131a` |
| **下载浪费缓存** | 360p preview 视频 + 删除段落时间轴（绿/红 + hover） | `3544422` `48ce671` |
| **热点不稳定** | TTLCache 30min + 60s 失败计数器快速失败 + baidu 加重 8/2 | `034a2d1` `48ce671` |

## 核心架构决策

- **深度思考开关**：默认开启（产品决策"质量优先"），localStorage 持久化，前端 `ReasoningToggle` 组件控制
- **preview 规格**：CRF 28 + b:v 600kbps + aac 64k + `+faststart`，10min 视频 ≈ 50MB
- **流式 SSE 协议**：OpenAI 兼容（`delta.content` / `delta.reasoning_content`）+ meta.parsed 收尾事件
- **git 节奏**：per-stage commit + push（基础设施 → 主功能 3 块 → 测试 → 技术债），不积压

## 关键文件入口

| 关注点 | 路径 |
|---|---|
| AI 流式核心 | `backend/core/ai_service.py`（`generate_stream` yield 事件对象） |
| 流式 Hook | `web/src/hooks/use-reasoning-stream-request.js` |
| ReasoningToggle | `web/src/components/common/ReasoningToggle.jsx` |
| 流式 SSE 端点 | `backend/api/copywriting.py` + `backend/api/shoot_script.py`（`/generate/stream`） |
| VideoEdit preview | `backend/api/media.py`（`/video-edit/{id}/preview`）+ `web/src/components/video-edit/VideoPreviewPlayer.jsx` |
| 时间轴可视化 | `web/src/components/video-edit/TimelineBar.jsx` |
| 热点缓存 | `backend/scrapers/cache.py` + `backend/scrapers/sixtys.py`（接入缓存） |
| 失败检测 + 加重 | `backend/core/platform_api.py`（`HotTopicSearchResult` + 失败计数器） |
| 降级 UI | `web/src/pages/insight/HotSearchPage.jsx` + `DegradedNotice` 组件 |
| 测试套件 | `backend/tests/e2e/test_stream_flow.py` + `test_video_edit_flow.py::TestPreview` + `test_trending_flow.py::TestTrendingV3Fields` + `test_cache.py` |

## 测试现状

- **核心相关 8 个测试文件**：111/111 全过（含新加 29 个）
- **完整 450 个测试**：446 pass + 4 skip + **11 fail**（剩 v3 老债）
- **剩 11 处 v3 老债**（用户选不修，需产品决策）：
  - `test_platform_api.py` 4 处：schema 缺 `platform` / `heat_index` 字段
  - `test_trending_service.py` 1 处：topic 缺 `platform` 属性
  - `test_calendar_service.py` 1 处：`CalendarEventResponse` 期望 id/created_at 非空但 DB 返回 None
  - `test_api_media.py` 2 处：media integration
  - `test_copywriting_flow.py` 4 处：rewrite 方向，依赖真实 AI 输出格式（flaky）

## 下次会话切入点

1. **修剩 11 处 v3 老债**（如产品决策允许 schema 加字段，或确认是 dead code 改测试断言）
2. **数字人**（[[project_phase2_digital_human]]）—— 阻塞在用户回答 3 个产品问题
3. **跑完整测试**确认没有新 flaky 引入

## 完整 plan + 设计文档

`.claude/plans/vivid-gliding-river.md` —— 完整 v3 冲刺 3 阶段实施方案（已落地）