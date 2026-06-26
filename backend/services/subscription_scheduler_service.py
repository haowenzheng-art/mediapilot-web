"""
订阅推送定时任务服务
每天扫描订阅并推送热点
"""
import logging
import asyncio
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from backend.config.database import SessionLocal
from backend.services.subscription_service import subscription_service

logger = logging.getLogger(__name__)


async def _fetch_hotspots_for_subscription(topic: str) -> List[Dict[str, Any]]:
    """
    异步获取话题的热点数据

    Args:
        topic: 订阅话题

    Returns:
        热点数据列表
    """
    from backend.services.trending_service_typed import TrendingService
    trending_service = TrendingService()

    result = await trending_service.search(
        keyword=topic,
        platforms=['baidu', 'weibo', 'zhihu', 'douyin', 'xiaohongshu'],
        days=1
    )

    if not result or not result.hot_topics:
        return []

    hotspot_data = [
        {
            'platform': ht.source or 'unknown',
            'title': ht.title,
            'summary': ht.summary,
            'url': ht.source_url,
            'heat_index': ht.heat_value,
            'trend': ht.trend_direction,
            'published_at': ht.published_at.isoformat() if ht.published_at else None
        }
        for ht in result.hot_topics[:5]
    ]

    return hotspot_data


async def _push_all_due_subscriptions(db: Session, due_subscriptions) -> None:
    """
    在同一个 event loop 里批量处理所有到期订阅

    避免 scheduled_subscription_push 在循环里反复 asyncio.run()，
    导致 TrendingService 共享的 aiohttp session 在 loop 关闭后失效。
    """
    for sub in due_subscriptions:
        try:
            hotspot_data = await _fetch_hotspots_for_subscription(sub.topic)

            if hotspot_data:
                push_record = subscription_service.create_push_record(
                    db=db,
                    subscription_id=sub.id,
                    topic=sub.topic,
                    hot_topic_data={'hotspots': hotspot_data}
                )
                subscription_service.update_subscription_push_time(db, sub.id)
                logger.info(
                    f"推送成功: 话题={sub.topic}, "
                    f"热点数={len(hotspot_data)}, 推送记录ID={push_record.id}"
                )
            else:
                logger.warning(f"话题 {sub.topic} 未找到热点，跳过推送")
        except Exception as e:
            logger.error(f"推送订阅失败: sub_id={sub.id}, topic={sub.topic}, error={e}")
            db.rollback()
            continue


async def run_push_cycle(db: Session) -> int:
    """
    推送周期核心逻辑（async）。

    供 async 端点直接 await，避免在 FastAPI event loop 里调 asyncio.run()。

    Returns:
        处理的推送数量
    """
    due_subscriptions = subscription_service.get_due_subscriptions(db)
    if not due_subscriptions:
        logger.info("没有需要推送的订阅")
        return 0
    logger.info(f"开始推送任务，共 {len(due_subscriptions)} 个订阅")
    await _push_all_due_subscriptions(db, due_subscriptions)
    logger.info("推送任务完成")
    return len(due_subscriptions)


def scheduled_subscription_push():
    """
    定时任务：扫描到期订阅并推送热点

    APScheduler 同步入口。创建独立 event loop 跑完整推送周期。
    不要在已运行的 event loop 里调（用 run_push_cycle 代替）。
    """
    db = SessionLocal()
    try:
        asyncio.run(run_push_cycle(db))
    except Exception as e:
        logger.error(f"推送任务执行失败: {e}", exc_info=True)
    finally:
        db.close()


def schedule_push_tasks(scheduler):
    """
    配置定时推送任务

    Args:
        scheduler: APScheduler 实例
    """
    scheduler.add_job(
        scheduled_subscription_push,
        'cron',
        hour=8,
        minute=0,
        id='subscription_push',
        replace_existing=True,
    )
    logger.info("订阅推送任务已调度：每天 08:00 执行")


def test_push_immediately():
    """测试：立即执行推送任务"""
    logger.info("执行测试推送任务...")
    scheduled_subscription_push()
