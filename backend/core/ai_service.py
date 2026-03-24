
"""
MediaPilot AI服务模块
支持多种AI提供商: Claude, GPT, 火山方舟
"""
import json
import re
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod


class AIService(ABC):
    """AI服务抽象基类"""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查服务是否可用"""
        pass


class AnthropicService(AIService):
    """Anthropic Claude服务"""

    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key
        self.model = model
        self.client = None
        self._init_client()

    def _init_client(self):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            self.client = None

    def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        if self.client:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        return ""

    def is_available(self) -> bool:
        return self.client is not None


class OpenAIService(AIService):
    """OpenAI兼容服务"""

    def __init__(self, api_key: str, base_url: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.client = None
        self._init_client()

    def _init_client(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            self.client = None

    def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        if self.client:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        return ""

    def is_available(self) -> bool:
        return self.client is not None


class ArkService(AIService):
    """火山方舟服务"""

    def __init__(self, api_key: str, base_url: str, model: str = "doubao-seed-2-0-pro-260215"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        try:
            import requests
            # 如果base_url已经包含/responses，就不要重复添加
            if self.base_url.endswith("/responses"):
                url = self.base_url
            else:
                url = f"{self.base_url}/responses"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model,
                "input": [{
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt}]
                }]
            }
            # 发送请求（不打印调试信息避免编码问题）
            response = requests.post(url, headers=headers, json=data, timeout=60)
            if response.status_code == 200:
                result = response.json()
                if "output" in result:
                    for content in result.get("output", []):
                        if content.get("type") == "message":
                            for msg_content in content.get("content", []):
                                if msg_content.get("type") == "output_text":
                                    return msg_content.get("text", "")
        except Exception as e:
            # 静默处理异常，避免编码问题
            pass
        return ""

    def is_available(self) -> bool:
        return self.api_key is not None and len(self.api_key) > 0


class AIServiceManager:
    """AI服务管理器"""

    def __init__(self):
        self.services: Dict[str, AIService] = {}
        self.current_provider: str = "anthropic"

    def configure_service(self, provider: str, api_key: str,
                          base_url: Optional[str] = None,
                          model: Optional[str] = None):
        """配置AI服务"""
        if provider == "anthropic":
            service = AnthropicService(api_key, model or "claude-3-haiku-20240307")
        elif provider == "openai":
            service = OpenAIService(api_key, base_url or "https://api.openai.com/v1", model or "gpt-3.5-turbo")
        elif provider == "ark":
            service = ArkService(api_key, base_url or "https://ark.cn-beijing.volces.com/api/v3",
                                 model or "doubao-seed-2-0-pro-260215")
        else:
            raise ValueError(f"不支持的AI提供商: {provider}")

        self.services[provider] = service
        self.current_provider = provider

    def get_current_service(self) -> Optional[AIService]:
        """获取当前AI服务"""
        return self.services.get(self.current_provider)

    def generate(self, prompt: str, **kwargs) -> str:
        """使用当前服务生成内容"""
        service = self.get_current_service()
        if service and service.is_available():
            return service.generate(prompt, **kwargs)
        return ""

    def generate_content_script(self, topic: str, platform: str,
                               duration: int, style: str) -> Dict[str, Any]:
        """生成分镜头脚本"""
        prompt = f"""你是一个专业的新媒体内容创作专家。请为以下主题创作短视频分镜头脚本。

主题: {topic}
平台: {platform}
目标时长: {duration}秒
风格: {style}

请返回JSON格式，不要其他文字:
{{
    "script": [
        {{
            "scene": 1,
            "duration": "0:00-0:05",
            "visual": "画面描述",
            "audio": "台词",
            "notes": "注意事项"
        }}
    ],
    "copywriting": {{
        "title": "爆款标题",
        "hooks": ["钩子1", "钩子2", "钩子3"],
        "call_to_action": "引导语",
        "tags": ["#标签1", "#标签2"]
    }}
}}
"""
        response = self.generate(prompt, max_tokens=3000)
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        return {}

    def rewrite_transcript(self, transcript: str, style: str,
                        target_duration: int) -> str:
        """改写逐字稿"""
        prompt = f"""请将以下视频逐字稿改写成{style}风格，目标时长约{target_duration}秒。

原文:
{transcript}

请直接返回改写后的文案。
"""
        return self.generate(prompt, max_tokens=1500)

    def generate_outline(self, transcript: str) -> List[Dict[str, str]]:
        """生成大纲"""
        prompt = f"""请为以下文字内容生成结构化大纲，返回JSON格式:

内容:
{transcript}

请返回:
{{
    "outline": [
        {{"section": "1", "title": "标题", "summary": "摘要"}},
        {{"section": "2", "title": "标题", "summary": "摘要"}}
    ]
}}
"""
        response = self.generate(prompt, max_tokens=1500)
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("outline", [])
        except Exception:
            pass
        return []


# 全局AI服务管理器实例
ai_manager = AIServiceManager()

