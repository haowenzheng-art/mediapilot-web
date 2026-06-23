"""
用户偏好设置 API
存储 theme / language / notification 等跨设备同步项
"""
from typing import Any, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.api.dependencies import get_current_user
from backend.models.database.tables import UserTable
from backend.utils.api_response import success_response

router = APIRouter(prefix="/user/preferences", tags=["用户偏好"])


# 允许写入的键白名单 + 默认值，防止前端瞎塞东西
_DEFAULTS: dict[str, Any] = {
    "theme": "dark",          # dark / light / auto
    "language": "zh-CN",      # zh-CN / en-US
    "notifications": True,    # 推送通知开关
    "auto_save": True,        # 编辑器自动保存
    "default_platform": "douyin",  # douyin / xiaohongshu / bilibili
}
_ALLOWED_KEYS = set(_DEFAULTS.keys())


class PreferencesUpdate(BaseModel):
    """偏好更新请求 - 部分更新，未传的键保持原值"""
    theme: Optional[str] = Field(None, pattern="^(dark|light|auto)$")
    language: Optional[str] = Field(None, pattern="^(zh-CN|en-US)$")
    notifications: Optional[bool] = None
    auto_save: Optional[bool] = None
    default_platform: Optional[str] = Field(None, pattern="^(douyin|xiaohongshu|bilibili)$")


def _resolve_prefs(user: UserTable) -> dict[str, Any]:
    """合并默认值 + 用户已存储的偏好，未配置项走默认"""
    stored = user.preferences or {}
    merged = {**_DEFAULTS, **{k: v for k, v in stored.items() if k in _ALLOWED_KEYS}}
    return merged


@router.get("")
def get_preferences(
    user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """读取当前用户偏好（含默认值填充）"""
    return success_response(data={"preferences": _resolve_prefs(user)})


@router.put("")
def update_preferences(
    payload: PreferencesUpdate,
    user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """部分更新偏好。未传字段保持原值。"""
    current = dict(user.preferences or {})
    incoming = payload.model_dump(exclude_none=True)
    current.update(incoming)
    user.preferences = current
    db.commit()
    db.refresh(user)
    return success_response(data={"preferences": _resolve_prefs(user)})


@router.post("/reset")
def reset_preferences(
    user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """重置为默认值"""
    user.preferences = {}
    db.commit()
    db.refresh(user)
    return success_response(data={"preferences": _resolve_prefs(user)})
