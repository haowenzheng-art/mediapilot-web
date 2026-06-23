"""
小红书视频信息 — Playwright 真实浏览器解析

为什么用 Playwright：
XHS 用 JS 加密签名（X-S/X-T）+ 设备指纹，httpx + cookie 都过不了风控。
真实浏览器加载页面后等 __INITIAL_STATE__ 注入完成，直接读 JS 全局变量取数据。

工作流：
1. headless chromium 打开 https://www.xiaohongshu.com/explore/{note_id}
2. 等 noteDetailMap 注入到 window.__INITIAL_STATE__
3. 通过 page.evaluate 拿 note JSON，映射到 VideoInfo 字段

支持短链 xhslink.com：先 follow redirect 拿真实 URL。
"""
import asyncio
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


async def fetch_xhs_note_via_playwright(video_url: str, timeout_ms: int = 15000) -> Optional[dict]:
    """
    用 Playwright 解析小红书笔记/视频信息。

    返回字段与 VideoInfo 兼容；任何异常都返回 None 让上层走降级。
    """
    try:
        from playwright.async_api import async_playwright, TimeoutError as PWTimeout
    except ImportError:
        logger.warning("playwright 未安装，无法解析小红书")
        return None

    # 提取 note_id
    note_id = _extract_note_id(video_url)
    target_url = video_url
    if not note_id and "xhslink.com" in video_url:
        # 短链需要先重定向取真实 URL
        try:
            import httpx
            async with httpx.AsyncClient(timeout=8, follow_redirects=False) as client:
                r = await client.get(video_url, headers={"User-Agent": "Mozilla/5.0"})
                location = r.headers.get("location", "")
                note_id = _extract_note_id(location)
                if note_id:
                    target_url = location
        except Exception as e:
            logger.warning(f"xhslink 短链展开失败: {e}")

    if not note_id:
        logger.warning(f"无法从 URL 提取 note_id: {video_url}")
        return None

    target_url = f"https://www.xiaohongshu.com/explore/{note_id}"

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )
            try:
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 800},
                    locale="zh-CN",
                )
                page = await context.new_page()
                await page.goto(target_url, wait_until="domcontentloaded", timeout=timeout_ms)
                # 等 __INITIAL_STATE__ 注入并包含 noteDetailMap
                try:
                    await page.wait_for_function(
                        f"""() => {{
                            const s = window.__INITIAL_STATE__;
                            if (!s) return false;
                            const m = s.note && s.note.noteDetailMap;
                            return m && m["{note_id}"] && m["{note_id}"].note;
                        }}""",
                        timeout=timeout_ms,
                    )
                except PWTimeout:
                    logger.warning(f"等待 noteDetailMap 超时: {note_id}")
                    return None

                note_data = await page.evaluate(
                    f"""() => {{
                        const note = window.__INITIAL_STATE__.note.noteDetailMap["{note_id}"].note;
                        return {{
                            title: note.title || "",
                            desc: note.desc || "",
                            type: note.type || "",
                            likedCount: (note.interactInfo && note.interactInfo.likedCount) || "0",
                            commentCount: (note.interactInfo && note.interactInfo.commentCount) || "0",
                            collectedCount: (note.interactInfo && note.interactInfo.collectedCount) || "0",
                            duration: (note.video && note.video.capa && note.video.capa.duration) || 0,
                            cover: (note.imageList && note.imageList[0] && (note.imageList[0].urlDefault || note.imageList[0].url)) || "",
                            time: note.time || 0,
                        }};
                    }}"""
                )
            finally:
                await browser.close()

        title = (note_data.get("title") or "").strip()
        desc = (note_data.get("desc") or "").strip()
        if not title and not desc:
            return None

        return {
            "url": target_url,
            "platform": "xiaohongshu",
            "video_id": note_id,
            "title": (title or desc[:50])[:200],
            "description": (desc or title)[:500],
            "thumbnail_url": note_data.get("cover", ""),
            "duration": int(note_data.get("duration") or 0),
            "view_count": _parse_count(note_data.get("collectedCount")),
            "like_count": _parse_count(note_data.get("likedCount")),
            "comment_count": _parse_count(note_data.get("commentCount")),
            "published_at": str(note_data.get("time") or ""),
        }
    except Exception as e:
        logger.warning(f"Playwright 解析小红书失败: {type(e).__name__}: {e}")
        return None


def _extract_note_id(url: str) -> Optional[str]:
    if not url:
        return None
    if "/explore/" in url:
        return url.split("/explore/")[1].split("?")[0].split("/")[0]
    if "/discovery/item/" in url:
        return url.split("/discovery/item/")[1].split("?")[0].split("/")[0]
    return None


def _parse_count(v) -> int:
    """小红书计数可能是 '1.2w' / '1234' / int，统一转 int"""
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    if not isinstance(v, str):
        return 0
    s = v.strip().lower().replace(",", "")
    if not s:
        return 0
    try:
        if s.endswith("w"):
            return int(float(s[:-1]) * 10000)
        if s.endswith("k"):
            return int(float(s[:-1]) * 1000)
        return int(float(s))
    except ValueError:
        return 0
