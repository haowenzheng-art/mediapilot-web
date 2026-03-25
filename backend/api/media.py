"""
媒体处理路由
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from models.schemas.response import APIResponse
from services.media_service import MediaService
from config.settings import get_upload_dir

router = APIRouter(prefix="/media", tags=["媒体处理"])

# 初始化服务
media_service = MediaService(get_upload_dir())


@router.post("/upload")
async def upload_media(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """上传音视频文件"""
    content = await file.read()
    result = await media_service.upload_and_process(content, file.filename)
    return APIResponse(data=result)


@router.get("/{task_id}/status")
async def get_media_status(task_id: str):
    """获取媒体处理状态"""
    if not media_service.task_exists(task_id):
        raise HTTPException(status_code=404, detail="任务不存在")
    result = await media_service.get_status(task_id)
    return APIResponse(data=result)


@router.get("/{task_id}/result")
async def get_media_result(task_id: str):
    """获取媒体处理结果"""
    if not media_service.task_exists(task_id):
        raise HTTPException(status_code=404, detail="任务不存在")
    result = await media_service.get_result(task_id)
    return APIResponse(data=result)
