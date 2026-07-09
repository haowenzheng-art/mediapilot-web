"""
视频分析业务逻辑
"""
import os
import tempfile
import logging
from typing import List

from backend.models.schemas.response import (
    VideoInfo,
    VideoTranscriptResponse,
    TranscriptLine,
)

logger = logging.getLogger(__name__)


class VideoService:
    """视频分析服务"""

    def __init__(self):
        pass

    async def _fetch_bilibili_basic(self, video_url: str) -> dict | None:
        """从 B 站公开 API 获取基础信息（封面、标题），不依赖 yt-dlp"""
        import httpx
        import re

        # 提取 bvid 或 aid
        bvid = None
        aid = None
        if "/video/" in video_url:
            part = video_url.split("/video/")[1].split("?")[0].split("/")[0]
            if part.startswith(("BV", "bv")):
                bvid = part
            else:
                aid = part

        api_url = ""
        if bvid:
            api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        elif aid:
            api_url = f"https://api.bilibili.com/x/web-interface/view?aid={aid}"
        else:
            return None

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    api_url,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; MediaPilot/1.0)", "Referer": "https://www.bilibili.com/"},
                )
                if r.status_code != 200:
                    return None
                data = r.json()
                if data.get("code") != 0:
                    return None
                v = data["data"]
                # 提取 video_id
                vid = v.get("bvid") or str(v.get("aid", ""))
                return {
                    "url": video_url,
                    "platform": "bilibili",
                    "video_id": vid,
                    "title": v.get("title", ""),
                    "description": (v.get("desc") or "")[:500],
                    "thumbnail_url": v.get("pic", ""),
                    "duration": v.get("duration", 0),
                    "view_count": v.get("stat", {}).get("view", 0),
                    "like_count": v.get("stat", {}).get("like", 0),
                    "comment_count": v.get("stat", {}).get("reply", 0),
                    "published_at": str(v.get("pubdate", "")),
                }
        except Exception as e:
            logger.warning(f"B站API调用失败: {e}")
            return None

    async def _fetch_douyin_basic(self, video_url: str) -> dict | None:
        """从抖音公开页面抓取基础信息"""
        import httpx
        import re

        try:
            # 尝试从 URL 提取 video_id
            # 抖音 URL 格式: https://www.douyin.com/video/728491238479
            video_id = None
            if "/video/" in video_url:
                video_id = video_url.split("/video/")[1].split("?")[0].split("/")[0]
            elif "/note/" in video_url:
                video_id = video_url.split("/note/")[1].split("?")[0].split("/")[0]

            if not video_id:
                return None

            # 尝试抖音公开接口
            api_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}"
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    api_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": "https://www.douyin.com/",
                    },
                )
                if r.status_code != 200:
                    return None
                data = r.json()
                aweme = data.get("aweme_detail") or {}
                stat = aweme.get("statistics", {}) or {}
                video_info = aweme.get("video", {}) or {}
                cover = video_info.get("cover", {}) or {}

                return {
                    "url": video_url,
                    "platform": "douyin",
                    "video_id": video_id,
                    "title": aweme.get("desc", "").split("\n")[0][:200] or "抖音视频",
                    "description": (aweme.get("desc") or "")[:500],
                    "thumbnail_url": cover.get("url_list", [""])[0] if cover.get("url_list") else "",
                    "duration": stat.get("duration", 0) or 0,
                    "view_count": stat.get("play_count", 0) or 0,
                    "like_count": stat.get("digg_count", 0) or 0,
                    "comment_count": stat.get("comment_count", 0) or 0,
                    "published_at": str(aweme.get("create_time", "")),
                }
        except Exception as e:
            logger.warning(f"抖音API调用失败: {e}")
            return None

    async def _fetch_weibo_basic(self, video_url: str) -> dict | None:
        """从微博公开页面抓取视频信息"""
        import httpx
        import re

        try:
            # 尝试解析微博视频页 title
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                r = await client.get(
                    video_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": "https://www.weibo.com/",
                    },
                )
                if r.status_code != 200:
                    return None
                html = r.text
                # 从 og 标签提取
                title = ""
                cover = ""
                m = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
                if m:
                    title = m.group(1)
                m = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
                if m:
                    cover = m.group(1)

                if not title:
                    return None

                video_id = video_url.split("/")[-1].split("?")[0]
                return {
                    "url": video_url,
                    "platform": "weibo",
                    "video_id": video_id,
                    "title": title,
                    "description": title,
                    "thumbnail_url": cover,
                    "duration": 0,
                    "view_count": 0,
                    "like_count": 0,
                    "comment_count": 0,
                    "published_at": "",
                }
        except Exception as e:
            logger.warning(f"微博API调用失败: {e}")
            return None

    async def _fetch_xiaohongshu_basic(self, video_url: str) -> dict | None:
        """从小红书页面解析。SPA 渲染没有 og 标签，需要解析 __INITIAL_STATE__ JSON。"""
        import httpx
        import re
        import json

        try:
            # 小红书页面：https://www.xiaohongshu.com/explore/NOTE_ID 或 /discovery/item/NOTE_ID
            note_id = None
            if "/explore/" in video_url:
                note_id = video_url.split("/explore/")[1].split("?")[0].split("/")[0]
            elif "/discovery/item/" in video_url:
                note_id = video_url.split("/discovery/item/")[1].split("?")[0].split("/")[0]
            elif "xhslink.com" in video_url:
                # 短链：先 follow redirect 拿真实 URL
                async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
                    r = await client.get(video_url, headers={"User-Agent": "Mozilla/5.0"})
                    location = r.headers.get("location", "")
                    if "/explore/" in location:
                        note_id = location.split("/explore/")[1].split("?")[0].split("/")[0]
                    elif "/discovery/item/" in location:
                        note_id = location.split("/discovery/item/")[1].split("?")[0].split("/")[0]

            if not note_id:
                return None

            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                r = await client.get(
                    f"https://www.xiaohongshu.com/explore/{note_id}",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Referer": "https://www.xiaohongshu.com/",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "zh-CN,zh;q=0.9",
                    },
                )
                if r.status_code != 200:
                    logger.warning(f"小红书页面返回 {r.status_code}")
                    return None
                html = r.text

                title = ""
                desc = ""
                cover = ""
                duration = 0
                view_count = 0
                like_count = 0
                comment_count = 0

                # 先尝试 og 标签（部分页面有）
                m = re.search(r'<meta\s+name="og:title"\s+content="([^"]+)"', html) \
                    or re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
                if m:
                    title = m.group(1)
                m = re.search(r'<meta\s+name="og:image"\s+content="([^"]+)"', html) \
                    or re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
                if m:
                    cover = m.group(1)
                m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html)
                if m:
                    desc = m.group(1)

                # 解析 window.__INITIAL_STATE__ JSON
                m = re.search(
                    r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*</script>',
                    html, re.DOTALL
                )
                if m:
                    try:
                        # 小红书会把 undefined 写进 JSON，替换成 null
                        raw = m.group(1).replace('undefined', 'null')
                        state = json.loads(raw)
                        # 路径不固定，尝试几个常见位置
                        note = (
                            state.get("note", {}).get("noteDetailMap", {}).get(note_id, {}).get("note")
                            or state.get("note", {}).get("note")
                            or {}
                        )
                        if note:
                            title = note.get("title") or title or (note.get("desc") or "")[:80]
                            desc = note.get("desc") or desc
                            interact = note.get("interactInfo", {}) or {}
                            like_count = int(interact.get("likedCount", 0) or 0)
                            comment_count = int(interact.get("commentCount", 0) or 0)
                            view_count = int(interact.get("collectedCount", 0) or 0)
                            video_info = note.get("video", {}) or {}
                            capa = video_info.get("capa", {}) or {}
                            duration = int(capa.get("duration", 0) or 0)
                            # 封面
                            image_list = note.get("imageList", []) or []
                            if image_list and not cover:
                                cover = image_list[0].get("urlDefault") or image_list[0].get("url", "")
                    except Exception as e:
                        logger.warning(f"小红书 __INITIAL_STATE__ 解析失败: {e}")

                if not title:
                    return None

                return {
                    "url": video_url,
                    "platform": "xiaohongshu",
                    "video_id": note_id,
                    "title": title[:200],
                    "description": (desc or title)[:500],
                    "thumbnail_url": cover,
                    "duration": duration,
                    "view_count": view_count,
                    "like_count": like_count,
                    "comment_count": comment_count,
                    "published_at": "",
                }
        except Exception as e:
            logger.warning(f"小红书API调用失败: {e}")
            return None

    async def fetch_video(self, video_url: str, platform: str) -> VideoInfo:
        """获取视频信息（使用yt-dlp，失败回退B站API，最后回退mock）"""
        try:
            import yt_dlp

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                # B站反爬：加 referer 和 UA
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.bilibili.com/',
                },
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)

                upload_date = info.get('upload_date', '')
                if upload_date and len(upload_date) == 8:
                    upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"

                result = {
                    "url": video_url,
                    "platform": platform,
                    "title": info.get('title', '未知标题'),
                    "description": info.get('description', ''),
                    "thumbnail_url": info.get('thumbnail', ''),
                    "duration": info.get('duration', 0),
                    "view_count": info.get('view_count', 0),
                    "like_count": info.get('like_count', 0),
                    "comment_count": info.get('comment_count', 0),
                    "published_at": upload_date or None,
                }

                # yt-dlp可能返回浮点数，转为整数
                result['duration'] = int(result.get('duration') or 0)
                result['view_count'] = int(result.get('view_count') or 0)
                result['like_count'] = int(result.get('like_count') or 0)
                result['comment_count'] = int(result.get('comment_count') or 0)

                # 从URL提取video_id
                if '/video/' in video_url:
                    result['video_id'] = video_url.split('/video/')[-1].split('?')[0]
                else:
                    result['video_id'] = video_url.split('/')[-1].split('?')[0]
                logger.info(f"yt-dlp获取视频信息成功: {result['title']} ({result['duration']}秒) video_id={result['video_id']}")
                return VideoInfo(**result)

        except Exception as e:
            logger.warning(f"yt-dlp获取视频信息失败: {e}，尝试平台官方 API")
            # 平台特定 fallback
            url_lower = video_url.lower()
            if platform == "bilibili" or "bilibili.com" in url_lower:
                bili = await self._fetch_bilibili_basic(video_url)
                if bili:
                    logger.info(f"B 站 API 获取成功: {bili['title']}")
                    return VideoInfo(**bili)
            if platform == "douyin" or "douyin.com" in url_lower:
                dy = await self._fetch_douyin_basic(video_url)
                if dy:
                    logger.info(f"抖音 API 获取成功: {dy['title']}")
                    return VideoInfo(**dy)
            if platform == "xiaohongshu" or "xiaohongshu.com" in url_lower or "xhslink.com" in url_lower:
                xhs = await self._fetch_xiaohongshu_basic(video_url)
                if xhs:
                    logger.info(f"小红书页面解析成功: {xhs['title']}")
                    return VideoInfo(**xhs)
                # httpx 解析失败 → 用 Playwright 真实浏览器（XHS 风控走 JS 签名，httpx 过不了）
                try:
                    from backend.core.xhs_playwright import fetch_xhs_note_via_playwright
                    xhs_pw = await fetch_xhs_note_via_playwright(video_url)
                    if xhs_pw:
                        logger.info(f"小红书 Playwright 解析成功: {xhs_pw['title']}")
                        return VideoInfo(**xhs_pw)
                except Exception as pw_e:
                    logger.warning(f"小红书 Playwright fallback 失败: {pw_e}")
            if platform == "weibo" or "weibo.com" in url_lower or "weibo.cn" in url_lower:
                wb = await self._fetch_weibo_basic(video_url)
                if wb:
                    logger.info(f"微博页面解析成功: {wb['title']}")
                    return VideoInfo(**wb)
            # 真实解析全部失败 — 不再回退 mock（会返回"爆款视频标题示例"等假数据，误导用户）
            # 小红书因强制登录态无法匿名访问；抖音/微博/小红书短链可能因反爬或链接失效
            hint = ""
            if "xiaohongshu" in url_lower or "xhslink.com" in url_lower:
                hint = "（小红书 Playwright 解析失败，可能笔记被删除、设为私密或风控临时拦截）"
            elif "douyin.com" in url_lower:
                hint = "（抖音反爬较强，建议使用完整 PC 端视频链接 https://www.douyin.com/video/xxx）"
            raise RuntimeError(f"无法解析视频信息: {e}{hint}")

    async def get_transcript(self, video_id: str) -> VideoTranscriptResponse:
        """获取视频逐字稿（yt-dlp提取音频 + whisper转写）

        数据真实性原则：失败时直接 raise RuntimeError 上报，
        不再回退"大家好今天给大家分享..."等假逐字稿（v4 D 任务清理）。
        """
        audio_file = os.path.join(tempfile.gettempdir(), f"audio_{video_id}")

        try:
            import yt_dlp
            from backend.utils.whisper_compat import patch as _patch_whisper_compat
            _patch_whisper_compat()
            import whisper

            # 1. 提取音频
            logger.info(f"开始提取音频: video_id={video_id}")
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': audio_file,
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }

            # 尝试常见的视频URL格式
            urls_to_try = [
                f"https://www.bilibili.com/video/{video_id}",
                video_id,  # 可能传入的就是完整URL
            ]

            downloaded = False
            for url in urls_to_try:
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.extract_info(url, download=True)
                    downloaded = True
                    break
                except Exception:
                    continue

            if not downloaded:
                raise RuntimeError(f"无法下载音频: {video_id}")

            # yt-dlp + FFmpegExtractAudio 会改变扩展名
            actual_audio = audio_file + ".mp3"
            if not os.path.exists(actual_audio):
                actual_audio = audio_file

            logger.info(f"音频提取完成: {actual_audio}")

            # 2. whisper转写
            logger.info("开始whisper转写...")
            model = whisper.load_model('base')
            # 与 TranscribeEngineManager 保持同一份配置：
            # initial_prompt 引导中文输出标点；condition_on_previous_text=False
            # 避免一旦某段丢标点后续整段无标点（openai/whisper#1390 #2026）
            result = model.transcribe(
                actual_audio,
                language='zh',
                initial_prompt="以下是普通话的句子，请输出带标点符号的简体中文。",
                condition_on_previous_text=False,
            )

            segments = result.get('segments', [])
            full_text = ' '.join([seg['text'].strip() for seg in segments])

            lines: List[TranscriptLine] = []
            for seg in segments:
                start = seg['start']
                time_str = f"{int(start // 60):02d}:{int(start % 60):02d}"
                lines.append(TranscriptLine(time=time_str, text=seg['text'].strip()))

            logger.info(f"转写完成，共{len(lines)}行")

            # 3. 删除临时音频文件
            for f in [actual_audio, audio_file]:
                if os.path.exists(f):
                    os.remove(f)
                    logger.info(f"已删除临时文件: {f}")

            return VideoTranscriptResponse(
                video_id=video_id,
                full_transcript=full_text,
                lines=lines
            )

        except Exception as e:
            logger.warning(f"视频转写失败: {e}")
            # 清理临时文件
            for f in [audio_file, audio_file + ".mp3"]:
                if os.path.exists(f):
                    os.remove(f)
                    logger.info(f"已清理临时文件: {f}")
            # 失败如实上报，不回退 mock 假数据
            raise RuntimeError(f"视频转写失败: {e}") from e
