
"""
MediaPilot API客户端
用于桌面端与后端API通信
"""
import requests
import json
from typing import Dict, Any, Optional, List, Tuple
from functools import lru_cache


class APIClient:
    """API客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _make_request(self, method: str, endpoint: str,
                     data: Optional[Dict] = None,
                     files: Optional[Dict] = None,
                     params: Optional[Dict] = None) -> Tuple[bool, Any]:
        """发送请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = self.session.get(url, params=params)
            elif method == "POST":
                if files:
                    response = self.session.post(url, files=files, data=data)
                else:
                    response = self.session.post(url, json=data, params=params)
            else:
                return False, "不支持的请求方法"

            if response.status_code == 200:
                result = response.json()
                return result.get("success", True), result.get("data") or result
            else:
                return False, f"请求失败: {response.status_code}"
        except Exception as e:
            return False, str(e)

    # ========== 热点搜索 ==========
    def search_trending(self, keyword: str, platforms: List[str],
                       days: int = 7) -> Tuple[bool, Any]:
        """搜索热点"""
        return self._make_request("POST", "/api/v1/trending/search", {
            "keyword": keyword,
            "platforms": platforms,
            "days": days
        })

    # ========== 对标账号 ==========
    def search_competitors(self, niche: str, platforms: List[str],
                          min_followers: int = 10000,
                          max_followers: int = 1000000,
                          min_avg_likes: int = 100) -> Tuple[bool, Any]:
        """搜索对标账号"""
        return self._make_request("POST", "/api/v1/competitors/search", {
            "niche": niche,
            "platforms": platforms,
            "min_followers": min_followers,
            "max_followers": max_followers,
            "min_avg_likes": min_avg_likes
        })

    def export_competitors(self, niche: str, save_path: str) -&gt; bool:
        """导出对标账号Excel"""
        try:
            url = f"{self.base_url}/api/v1/competitors/export?niche={niche}"
            response = self.session.get(url)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                return True
            return False
        except Exception:
            return False

    # ========== 视频分析 ==========
    def fetch_video(self, video_url: str, platform: str) -> Tuple[bool, Any]:
        """获取视频信息"""
        return self._make_request("POST", "/api/v1/video/fetch", {
            "video_url": video_url,
            "platform": platform
        })

    def get_video_transcript(self, video_id: str) -> Tuple[bool, Any]:
        """获取视频逐字稿"""
        return self._make_request("POST", "/api/v1/video/transcript",
                                  params={"video_id": video_id})

    def rewrite_transcript(self, transcript: str, style: str,
                          duration: int = 60) -> Tuple[bool, Any]:
        """改写逐字稿"""
        return self._make_request("POST", "/api/v1/video/rewrite", {
            "transcript": transcript,
            "style": style,
            "target_duration": duration
        })

    # ========== 内容生成 ==========
    def generate_content(self, topic: str, platform: str,
                        duration: int = 60, style: str = "professional") -> Tuple[bool, Any]:
        """生成内容"""
        return self._make_request("POST", "/api/v1/content/generate", {
            "topic": topic,
            "platform": platform,
            "duration": duration,
            "style": style
        })

    # ========== 音视频转写 ==========
    def upload_media(self, file_path: str) -> Tuple[bool, Any]:
        """上传媒体文件"""
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                return self._make_request("POST", "/api/v1/media/upload", files=files)
        except Exception as e:
            return False, str(e)

    def get_media_status(self, task_id: str) -> Tuple[bool, Any]:
        """获取媒体处理状态"""
        return self._make_request("GET", f"/api/v1/media/{task_id}/status")

    def get_media_result(self, task_id: str) -> Tuple[bool, Any]:
        """获取媒体处理结果"""
        return self._make_request("GET", f"/api/v1/media/{task_id}/result")

    # ========== AI配置 ==========
    def configure_ai(self, provider: str, api_key: str,
                    base_url: str = None, model: str = None) -> Tuple[bool, Any]:
        """配置AI服务"""
        return self._make_request("POST", "/api/v1/ai/configure", params={
            "provider": provider,
            "api_key": api_key,
            "base_url": base_url,
            "model": model
        })

    def check_health(self) -> bool:
        """检查后端服务状态"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False


# 全局API客户端实例
api_client = APIClient()

