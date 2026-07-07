"""
拍摄脚本生成路由
使用统一的 API 响应模型
"""
import json
import logging

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.models.domain.shoot_script import (
    ShootScriptRequest, ShootScriptResponse, ScriptExportRequest
)
from backend.models.schemas.api_response import ErrorCode
from backend.utils.api_response import (
    success_response,
    error_response
)
from backend.services.shoot_script_service import shoot_script_service
from backend.services.content_library_service import content_library_service
from backend.models.database.tables import UserTable
from backend.api.dependencies import get_current_user
from backend.services.auth_service_typed import auth_service
from backend.models.domain.content_library import ContentCreate, ContentType
from backend.config.settings import settings, ensure_dev_user

router = APIRouter(prefix="/shoot-script", tags=["拍摄脚本"])


@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return success_response(data={"status": "ok"}, message="拍摄脚本服务正常")


@router.post("/generate")
async def generate_shoot_script(
    request: ShootScriptRequest,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    生成拍摄脚本

    支持三个平台：
    - douyin: 抖音竖屏 60s
    - xiaohongshu: 小红书 3min
    - bilibili: B站横屏 5-10min

    支持三种风格：
    - energetic: 激情热血
    - relaxed: 轻松幽默
    - professional: 专业分析
    """
    user = current_user

    # 检查配额
    if not auth_service.check_quota(db, user.id, "generate_shoot_script"):
        return error_response(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"配额不足，当前余额: {user.quota_balance}",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    try:
        # 生成脚本
        result = await shoot_script_service.generate(request)

        # 保存到内容库
        try:
            content_create = ContentCreate(
                content_type=ContentType.SHOOT_SCRIPT,
                content_id=result.id,
                title=result.title,
                summary=result.topic,
                hot_topic_id=None,  # 脚本生成暂不关联热点
                hot_topic_title=None,
                hot_topic_source=None,
                mode=None,
                persona=request.persona,
                platform=result.platform.value,
                style=result.style.value
            )
            content_library_service.create_content(db, user.id, content_create)
        except Exception as e:
            # 内容库保存失败不影响脚本生成，只记录日志
            logger.warning(f"保存脚本到内容库失败: {e}")

        # 扣减配额
        auth_service.deduct_quota(db, user.id, "generate_shoot_script")

        return success_response(
            data=result,
            message="生成拍摄脚本成功"
        )
    except ValueError as e:
        return error_response(
            code=ErrorCode.INVALID_INPUT,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"生成拍摄脚本失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"生成拍摄脚本失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/generate/stream")
async def generate_shoot_script_stream(
    request: ShootScriptRequest,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    流式生成拍摄脚本（SSE）

    复用 /generate 的配额检查逻辑（先 check 不扣，流式完成后再扣）。
    异常时 refund_quota。
    事件格式与 copywriting/stream 一致：OpenAI 兼容 + reasoning_content + meta.parsed。
    """
    # 配额检查（先 check，流式完成后再 deduct）
    if not auth_service.check_quota(db, current_user.id, "generate_shoot_script"):
        return error_response(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"配额不足，当前余额: {current_user.quota_balance}",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    quota_deducted = False

    async def event_stream():
        nonlocal quota_deducted
        try:
            async for event in shoot_script_service.generate_stream(request):
                if event.get("type") == "content":
                    yield "data: " + json.dumps({
                        "choices": [{"delta": {"content": event["delta"]}}]
                    }, ensure_ascii=False) + "\n\n"
                elif event.get("type") == "reasoning":
                    yield "data: " + json.dumps({
                        "choices": [{"delta": {"reasoning_content": event["delta"]}}]
                    }, ensure_ascii=False) + "\n\n"
                elif event.get("type") == "meta":
                    # 解析成功后扣配额
                    if event.get("meta", {}).get("final") and not quota_deducted:
                        try:
                            auth_service.deduct_quota(db, current_user.id, "generate_shoot_script")
                            quota_deducted = True
                        except Exception as de:
                            logger.error(f"扣配额失败: {de}")
                    yield "data: " + json.dumps({
                        "choices": [{"delta": {}}],
                        "meta": event.get("meta", {}),
                    }, ensure_ascii=False) + "\n\n"
                elif event.get("type") == "error":
                    yield "data: " + json.dumps({"error": event.get("delta", "")}, ensure_ascii=False) + "\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"流式生成脚本失败: {e}")
            yield "data: " + json.dumps({"error": f"流式生成失败: {str(e)}"}, ensure_ascii=False) + "\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{script_id}")
async def get_shoot_script(
    script_id: str,
    db: Session = Depends(get_db)
):
    """
    获取拍摄脚本
    """
    try:
        script = shoot_script_service.get_script(script_id)
        if not script:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="脚本不存在",
                status_code=status.HTTP_404_NOT_FOUND
            )

        return success_response(
            data=script,
            message="获取脚本成功"
        )
    except Exception as e:
        logger.error(f"获取拍摄脚本失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取拍摄脚本失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/export")
async def export_shoot_script(
    request: ScriptExportRequest,
    db: Session = Depends(get_db)
):
    """
    导出拍摄脚本

    支持格式：
    - json: JSON格式
    - txt: 纯文本格式
    - csv: CSV格式
    """
    try:
        script = shoot_script_service.get_script(request.script_id)
        if not script:
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="脚本不存在",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # 根据格式导出
        if request.format == "json":
            content = _export_as_json(script)
            media_type = "application/json"
            filename = f"shoot_script_{request.script_id}.json"
        elif request.format == "txt":
            content = _export_as_txt(script)
            media_type = "text/plain"
            filename = f"shoot_script_{request.script_id}.txt"
        elif request.format == "csv":
            content = _export_as_csv(script)
            media_type = "text/csv"
            filename = f"shoot_script_{request.script_id}.csv"
        else:
            return error_response(
                code=ErrorCode.INVALID_INPUT,
                message="不支持的导出格式",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        from fastapi.responses import Response
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"导出拍摄脚本失败: {e}")
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"导出拍摄脚本失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _export_as_json(script: ShootScriptResponse) -> str:
    """导出为JSON格式"""
    # 用 Pydantic 自带序列化，处理 datetime
    return script.model_dump_json(indent=2)


def _export_as_txt(script: ShootScriptResponse) -> str:
    """导出为TXT格式"""
    lines = [
        f"拍摄脚本 - {script.topic}",
        f"平台: {script.platform.value}",
        f"风格: {script.style.value}",
        f"预计时长: {script.estimated_duration}",
        "",
        "=" * 50,
        "",
        "【标题】",
        script.title,
        "",
        "【钩子】",
        *[f"{i+1}. {hook}" for i, hook in enumerate(script.hooks)],
        "",
        "【行动号召】",
        script.call_to_action,
        "",
        "【标签】",
        ", ".join(script.tags),
        "",
        "=" * 50,
        "",
        "【分镜头脚本】",
        "",
    ]

    for shot in script.shots:
        lines.extend([
            f"镜头{shot.shot_number} [时长: {shot.duration}]",
            f"画面: {shot.visual_description}",
            f"台词: {shot.dialogue}",
            f"场景建议: {shot.scene_suggestion or ''}",
            f"运镜建议: {shot.camera_movement or ''}",
            ""
        ])

    return "\n".join(lines)


def _export_as_csv(script: ShootScriptResponse) -> str:
    """导出为CSV格式"""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # 写入脚本信息
    writer.writerow(["拍摄脚本信息", ""])
    writer.writerow(["话题", script.topic])
    writer.writerow(["平台", script.platform.value])
    writer.writerow(["风格", script.style.value])
    writer.writerow(["预计时长", script.estimated_duration])
    writer.writerow(["标题", script.title])
    writer.writerow(["行动号召", script.call_to_action])
    writer.writerow(["标签", ", ".join(script.tags)])
    writer.writerow([])

    # 写入钩子
    writer.writerow(["钩子", ""])
    for i, hook in enumerate(script.hooks):
        writer.writerow([f"{i+1}", hook])
    writer.writerow([])

    # 写入分镜头
    writer.writerow(["分镜头脚本", "", "", "", ""])
    writer.writerow(["镜头编号", "时长", "画面描述", "台词", "场景建议", "运镜建议"])
    for shot in script.shots:
        writer.writerow([
            shot.shot_number,
            shot.duration,
            shot.visual_description,
            shot.dialogue,
            shot.scene_suggestion or "",
            shot.camera_movement or ""
        ])

    return output.getvalue()
