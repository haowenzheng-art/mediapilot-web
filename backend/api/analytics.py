"""
Analytics API — 用户真实活动看板
基于 MediaPilot 内部数据（内容库 / 订阅推送 / 配额），
不假装拥有 外部 平台播放/粉丝 数据（那需要付费 API）。
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.api.dependencies import get_current_user
from backend.models.database.tables import (
    UserTable, ContentTable, SubscriptionTable, PushRecordTable
)
from backend.utils.api_response import success_response

router = APIRouter(prefix="/analytics", tags=["数据看板"])


def _day_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


@router.get("/dashboard")
def dashboard(
    days: int = Query(30, ge=7, le=90, description="窗口天数 7-90"),
    user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    用户真实创作看板：
    - overview: 内容/订阅/未读推送/剩余配额 4 个核心数
    - daily_content: 每日按 content_type 计数（窗口内补 0）
    - top_hot_topics: 用户用得最多的前 5 个热点
    - content_type_split: copywriting / shoot_script 各多少
    """
    since = datetime.utcnow() - timedelta(days=days)

    # ---- overview ----
    total_content = (
        db.query(func.count(ContentTable.id))
        .filter(ContentTable.user_id == user.id)
        .scalar() or 0
    )
    total_sub = (
        db.query(func.count(SubscriptionTable.id))
        .filter(SubscriptionTable.user_id == user.id)
        .scalar() or 0
    )
    unread_push = (
        db.query(func.count(PushRecordTable.id))
        .join(SubscriptionTable, PushRecordTable.subscription_id == SubscriptionTable.id)
        .filter(
            SubscriptionTable.user_id == user.id,
            PushRecordTable.status == "new",
        )
        .scalar() or 0
    )

    # ---- daily content (in window) ----
    rows = (
        db.query(
            func.date(ContentTable.created_at).label("d"),
            ContentTable.content_type,
            func.count(ContentTable.id).label("cnt"),
        )
        .filter(
            ContentTable.user_id == user.id,
            ContentTable.created_at >= since,
        )
        .group_by("d", ContentTable.content_type)
        .all()
    )
    bucket: dict[str, dict[str, int]] = {}
    for r in rows:
        # SQLAlchemy func.date 在 SQLite 下回 str；PG 下回 date 对象
        d = r.d if isinstance(r.d, str) else r.d.strftime("%Y-%m-%d")
        bucket.setdefault(d, {"copywriting": 0, "shoot_script": 0})
        if r.content_type in ("copywriting", "shoot_script"):
            bucket[d][r.content_type] = int(r.cnt)

    daily_content = []
    cursor = datetime.utcnow().date() - timedelta(days=days - 1)
    today = datetime.utcnow().date()
    while cursor <= today:
        key = cursor.strftime("%Y-%m-%d")
        item = bucket.get(key, {"copywriting": 0, "shoot_script": 0})
        daily_content.append({
            "date": key,
            "copywriting": item["copywriting"],
            "shoot_script": item["shoot_script"],
            "total": item["copywriting"] + item["shoot_script"],
        })
        cursor += timedelta(days=1)

    # ---- content_type split ----
    type_rows = (
        db.query(ContentTable.content_type, func.count(ContentTable.id))
        .filter(ContentTable.user_id == user.id)
        .group_by(ContentTable.content_type)
        .all()
    )
    type_split = {t: int(c) for t, c in type_rows}

    # ---- top hot topics by user activity ----
    top_rows = (
        db.query(
            ContentTable.hot_topic_id,
            ContentTable.hot_topic_title,
            ContentTable.hot_topic_source,
            func.count(ContentTable.id).label("cnt"),
        )
        .filter(
            ContentTable.user_id == user.id,
            ContentTable.hot_topic_id.isnot(None),
        )
        .group_by(ContentTable.hot_topic_id)
        .order_by(func.count(ContentTable.id).desc())
        .limit(5)
        .all()
    )
    top_hot_topics = [
        {
            "hot_topic_id": r.hot_topic_id,
            "title": r.hot_topic_title,
            "source": r.hot_topic_source,
            "content_count": int(r.cnt),
        }
        for r in top_rows
    ]

    return success_response(data={
        "window_days": days,
        "overview": {
            "total_content": total_content,
            "total_subscriptions": total_sub,
            "unread_push": unread_push,
            "quota_balance": user.quota_balance,
        },
        "daily_content": daily_content,
        "content_type_split": type_split,
        "top_hot_topics": top_hot_topics,
    })


@router.get("/health")
def health():
    return success_response(data={"status": "ok"})
