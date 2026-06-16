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
from backend.services.mock_data import MockDataService

logger = logging.getLogger(__name__)


class VideoService:
    """视频分析服务"""

    def __init__(self):
        self.mock_data = MockDataService()

    async def fetch_video(self, video_url: str, platform: str) -> VideoInfo:
        """获取视频信息（使用yt-dlp，失败回退mock）"""
        try:
            import yt_dlp

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
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
            logger.warning(f"yt-dlp获取视频信息失败，回退mock: {e}")
            video = self.mock_data.fetch_video(video_url, platform)
            return VideoInfo(**video)

    async def get_transcript(self, video_id: str) -> VideoTranscriptResponse:
        """获取视频逐字稿（yt-dlp提取音频 + whisper转写，失败回退mock）"""
        audio_file = os.path.join(tempfile.gettempdir(), f"audio_{video_id}")

        try:
            import yt_dlp
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
            result = model.transcribe(actual_audio, language='zh')

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
            logger.warning(f"视频转写失败，回退mock: {e}")
            # 清理临时文件
            for f in [audio_file, audio_file + ".mp3"]:
                if os.path.exists(f):
                    os.remove(f)
                    logger.info(f"已清理临时文件: {f}")

            transcript = self.mock_data.get_video_transcript(video_id)
            return VideoTranscriptResponse(
                video_id=video_id,
                full_transcript=transcript["full_transcript"],
                lines=[TranscriptLine(**l) for l in transcript["lines"]]
            )
