"""
MediaPilot AI服务模块
支持多种AI提供商: Claude, GPT, 火山方舟
"""
import json
import logging
import re
import httpx
from typing import Optional, Dict, Any, List, AsyncGenerator
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AIService(ABC):
    """AI服务抽象基类"""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本（异步）"""
        pass

    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查服务是否可用"""
        pass


class AnthropicService(AIService):
    """Anthropic Claude服务"""

    def __init__(
        self,
        api_key: str,
        model: str = "agnes-2.0-flash",
        timeout: int = 60,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = None
        self._init_client()

    def _init_client(self):
        try:
            import anthropic
            self.client = anthropic.Anthropic(
                api_key=self.api_key,
                timeout=self.timeout
            )
        except ImportError:
            self.client = None

    async def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        if not self.client:
            raise RuntimeError("Anthropic客户端未初始化，请检查 anthropic 包是否是否安装")

        import asyncio
        for attempt in range(self.max_retries):
            try:
                message = await asyncio.to_thread(
                    self.client.messages.create,
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
                else:
                    raise RuntimeError(f"AI生成失败: {str(e)}") from e
        return ""

    async def generate_stream(self, prompt: str, max_tokens: int = 2000, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        if not self.client:
            raise RuntimeError("Anthropic客户端未初始化，请检查 anthropic 包是否是否安装")

        import asyncio
        for attempt in range(self.max_retries):
            try:
                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                ) as stream:
                    for text in stream.text_stream:
                        yield text
                        await asyncio.sleep(0)  # 让出控制权
                return
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
                else:
                    raise RuntimeError(f"AI流式生成失败: {str(e)}") from e

    def is_available(self) -> bool:
        return self.client is not None and bool(self.api_key)


class OpenAIService(AIService):
    """OpenAI兼容服务"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "agnes-2.0-flash",
        timeout: int = 60,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = None
        self._init_client()

    def _init_client(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
        except ImportError:
            self.client = None

    async def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        if not self.client:
            raise RuntimeError("OpenAI客户端未初始化，请检查 openai 包是否安装")

        logger.info(f"OpenAI API请求: base_url={self.base_url}, model={self.model}")

        import asyncio
        for attempt in range(self.max_retries):
            try:
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"OpenAI API重试 {attempt + 1}/{self.max_retries}: {e}")
                    await asyncio.sleep(1 * (attempt + 1))
                else:
                    raise RuntimeError(f"AI生成失败: {str(e)}") from e
        return ""

    async def generate_stream(self, prompt: str, max_tokens: int = 2000, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        import asyncio
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": self.model,
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": max_tokens,
                            "temperature": 0.7,
                            "stream": True
                        }
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]
                                if data == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data)
                                    content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    if content:
                                        yield content
                                        await asyncio.sleep(0)
                                except json.JSONDecodeError:
                                    pass
                        return
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
                else:
                    raise RuntimeError(f"AI流式生成失败: {str(e)}") from e

    def is_available(self) -> bool:
        return self.client is not None and bool(self.api_key)


class ArkService(AIService):
    """火山方舟服务"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "agnes-2.0-flash",
        timeout: int = 60,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    async def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        try:
            import requests
        except ImportError:
            raise RuntimeError("requests包未安装")

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

        logger.info(f"Ark API请求: url={url}, model={self.model}")

        import asyncio
        for attempt in range(self.max_retries):
            try:
                response = await asyncio.to_thread(
                    requests.post,
                    url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                if response.status_code != 200:
                    logger.error(f"Ark API错误: status={response.status_code}, body={response.text[:500]}")
                response.raise_for_status()
                result = response.json()
                if "output" in result:
                    for content in result.get("output", []):
                        if content.get("type") == "message":
                            for msg_content in content.get("content", []):
                                if msg_content.get("type") == "output_text":
                                    return msg_content.get("text", "")
                raise RuntimeError("AI响应格式错误: 未找到输出文本")
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Ark API重试 {attempt + 1}/{self.max_retries}: {e}")
                    await asyncio.sleep(1 * (attempt + 1))
                else:
                    raise RuntimeError(f"AI生成失败: {str(e)}") from e
        return ""

    async def generate_stream(self, prompt: str, max_tokens: int = 2000, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成文本 - 火山方舟支持流式输出"""
        import asyncio

        # 如果base_url已经包含/responses，就不要重复添加
        if self.base_url.endswith("/responses"):
            url = self.base_url
        else:
            url = f"{self.base_url}/responses"

        logger.info(f"Ark Stream API请求: url={url}, model={self.model}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "input": [{
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}]
            }],
            "parameters": {
                "max_tokens": max_tokens,
                "result_format": "text"
            },
            "stream": True
        }

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    async with client.stream(
                        "POST",
                        url,
                        headers=headers,
                        json=data
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line.startswith("data:"):
                                data_str = line[5:].strip()
                                if not data_str:
                                    continue
                                try:
                                    chunk = json.loads(data_str)
                                    # 火山方舟流式响应格式
                                    for content in chunk.get("output", []):
                                        if content.get("type") == "message":
                                            for msg_content in content.get("content", []):
                                                if msg_content.get("type") == "output_text":
                                                    text = msg_content.get("text", "")
                                                    if text:
                                                        yield text
                                                        await asyncio.sleep(0)
                                except json.JSONDecodeError:
                                    pass
                        return
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
                else:
                    raise RuntimeError(f"AI流式生成失败: {str(e)}") from e

    def is_available(self) -> bool:
        return self.api_key is not None and len(self.api_key) > 0


class AIServiceManager:
    """AI服务管理器"""

    def __init__(self):
        self.services: Dict[str, AIService] = {}
        self.current_provider: Optional[str] = None
        self._initialized = False

    def configure(
        self,
        provider: str,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3
    ):
        """配置AI服务"""
        if provider == "anthropic":
            service = AnthropicService(
                api_key,
                model or "ark-code-latest",
                timeout,
                max_retries
            )
        elif provider == "openai":
            resolved_url = base_url or "https://apihub.agnes-ai.com/v1"
            resolved_model = model or "agnes-2.0-flash"
            logger.info(f"配置OpenAI服务: base_url={resolved_url}, model={resolved_model}")
            service = OpenAIService(
                api_key,
                resolved_url,
                resolved_model,
                timeout,
                max_retries
            )
        elif provider == "ark":
            resolved_url = base_url or "https://apihub.agnes-ai.com/v1"
            resolved_model = model or "agnes-2.0-flash"
            logger.info(f"配置Ark服务: base_url={resolved_url}, model={resolved_model}")
            service = ArkService(
                api_key,
                resolved_url,
                resolved_model,
                timeout,
                max_retries
            )
        else:
            raise ValueError(f"不支持的AI提供商: {provider}")

        self.services[provider] = service
        self.current_provider = provider
        self._initialized = True
        logger.info(f"AI服务已切换到: {provider}")

    def get_current_service(self) -> Optional[AIService]:
        """获取当前AI服务"""
        return self.services.get(self.current_provider) if self.current_provider else None

    async def generate(self, prompt: str, **kwargs) -> str:
        """使用当前服务生成内容（异步）"""
        service = self.get_current_service()
        if not service:
            raise RuntimeError("AI服务未配置")
        if not service.is_available():
            raise RuntimeError("AI服务不可用，请检查API密钥配置")
        return await service.generate(prompt, **kwargs)

    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """使用当前服务流式生成内容"""
        service = self.get_current_service()
        if not service:
            raise RuntimeError("AI服务未配置")
        if not service.is_available():
            raise RuntimeError("AI服务不可用，请检查API密钥配置")
        async for chunk in service.generate_stream(prompt, **kwargs):
            yield chunk

    def is_available(self) -> bool:
        """检查当前服务是否可用"""
        service = self.get_current_service()
        return service is not None and service.is_available()

    async def generate_content_script(self, topic: str, platform: str,
                               duration: int, style: str) -> Dict[str, Any]:
        """生成分镜头脚本（异步）"""
        prompt = f"""你是一个专业的新媒体内容创作专家。请为以下主题创作短视频分镜头脚本。

主题: {topic}
平台: {platform}
目标时长: {duration}秒
风格: {style}

请直接返回JSON格式，不要使用markdown代码块包装，不要其他文字:
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
        response = await self.generate(prompt, max_tokens=3000)
        try:
            # 先尝试提取 markdown 代码块（兼容Ark API的响应格式）
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                return json.loads(json_str)
            # 如果没有 markdown 代码块，回退到原来的方式
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            raise RuntimeError(f"解析AI响应失败: {str(e)}")
        raise RuntimeError("AI响应未包含有效JSON")

    async def rewrite_transcript(self, transcript: str, style: str,
                        target_duration: int) -> str:
        """改写逐字稿（异步）"""
        prompt = f"""请将以下视频逐字稿改写成{style}风格，目标时长约{target_duration}秒。

原文:
{transcript}

请直接返回改写后的文案。
"""
        return await self.generate(prompt, max_tokens=1500)

    async def generate_outline(self, transcript: str) -> List[Dict[str, str]]:
        """生成大纲（异步）"""
        prompt = f"""请为以下文字内容生成结构化大纲，直接返回JSON格式，不要使用markdown代码块。

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
        response = await self.generate(prompt, max_tokens=1500)
        try:
            # 先尝试提取 markdown 代码块（兼容Ark API的响应格式）
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                data = json.loads(json_str)
                return data.get("outline", [])
            # 如果没有 markdown 代码块，回退到原来的方式
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("outline", [])
        except Exception as e:
            raise RuntimeError(f"解析AI响应失败: {str(e)}")
        raise RuntimeError("AI响应未包含有效JSON")


# 全局AI服务管理器实例
ai_manager = AIServiceManager()
