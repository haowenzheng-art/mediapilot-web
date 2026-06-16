"""
内容生成路由
使用统一的 API 响应模型
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.services.content_service import ContentService
from backend.models.schemas.api_response import ErrorCode
from backend.utils.api_response import success_response, error_response
from backend.core.ai_service import ai_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["内容生成"])

content_service = ContentService()


class GenerateRequest(BaseModel):
    topic: str
    platform: str = "douyin"
    duration: int = 60
    style: str = "professional"


class RewriteRequest(BaseModel):
    transcript: str
    style: str = "简洁"
    target_duration: Optional[int] = None


@router.post("/generate")
async def generate_content(
    req: GenerateRequest,
    db: Session = Depends(get_db)
):
    """
    生成分镜头脚本和文案
    不需要认证，使用mock数据或AI服务
    """
    mock_script = {
        "script": [
            {"scene": 1, "duration": "0:00-0:05", "visual": "开场画面", "audio": f"今天聊聊{req.topic}", "notes": "吸引注意力"},
            {"scene": 2, "duration": "0:05-0:20", "visual": "主体内容", "audio": "核心要点讲解", "notes": "重点强调"},
            {"scene": 3, "duration": "0:20-0:30", "visual": "结尾画面", "audio": "记得点赞关注", "notes": "引导互动"},
        ],
        "copywriting": {
            "title": req.topic,
            "hooks": [f"你知道{req.topic}的秘密吗？", f"关于{req.topic}，90%的人都不知道", f"3分钟带你了解{req.topic}"],
            "call_to_action": "点赞收藏，下期更精彩！",
            "tags": [req.topic, "干货分享", "必看"],
        }
    }

    try:
        if ai_manager.is_available():
            script_data = await ai_manager.generate_content_script(
                topic=req.topic,
                platform=req.platform,
                duration=req.duration,
                style=req.style
            )
        else:
            script_data = mock_script

        return success_response(
            data=script_data,
            message=f"生成内容成功: {req.topic}"
        )
    except Exception as e:
        logger.warning(f"AI生成失败，回退到mock数据: {e}")
        return success_response(
            data=mock_script,
            message=f"AI服务暂不可用，已返回示例数据"
        )


@router.post("/rewrite")
async def rewrite_transcript(
    req: RewriteRequest,
    db: Session = Depends(get_db)
):
    """
    改写视频文案
    不需要认证，AI不可用时返回mock数据
    """
    mock_result = {
        "original": req.transcript,
        "rewritten": f"改写后的文案（{req.style}风格）: {req.transcript[:50]}..."
    }

    try:
        if ai_manager.is_available():
            rewritten = await ai_manager.rewrite_transcript(
                req.transcript,
                req.style,
                req.target_duration or 60
            )
            return success_response(
                data={"original": req.transcript, "rewritten": rewritten},
                message="改写文案成功"
            )
        else:
            return success_response(
                data=mock_result,
                message="AI服务暂不可用，已返回示例数据"
            )
    except Exception as e:
        logger.warning(f"AI改写失败，回退到mock数据: {e}")
        return success_response(
            data=mock_result,
            message="AI服务暂不可用，已返回示例数据"
        )
