"""
订阅推送定时任务服务
每天扫描订阅并推送热点
"""
import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime
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
    # 动态导入避免循环引用
    from backend.services.trending_service_typed import TrendingService
    trending_service = TrendingService()

    result = await trending_service.search(
        keyword=topic,
        platforms=['baidu', 'weibo', 'zhihu', 'douyin', 'xiaohongshu'],
        days=1
    )

    if not result or not result.hot_topics:
        return []

    # 转换热点数据为推送格式
    hotspot_data = [
        {
            'platform': topic.platform or topic.source or 'unknown',
            'title': topic.title,
            'summary': topic.summary,
            'url': topic.source_url or topic.url,
            'heat_index': topic.heat_value,
            'trend': topic.trend_direction,
            'published_at': topic.published_at
        }
        for topic in result.hot_topics[:5]  # 只推送前5条
    ]

    return hotspot_data


def scheduled_subscription_push():
    """
    定时任务：扫描到期订阅并推送热点

    1. 获取所有到期的订阅（next_push_at <= 当前时间）
    2. 对每个订阅，搜索相关热点
    3. 创建推送记录
    4. 更新订阅的下次推送时间
    """
    db = SessionLocal()
    try:
        # 获取需要推送的订阅
        due_subscriptions = subscription_service.get_due_subscriptions(db)

        if not due_subscriptions:
            logger.info("没有需要推送的订阅")
            return

        logger.info(f"开始推送任务，共 {len(due_subscriptions)} 个订阅")

        for sub in due_subscriptions:
            try:
                # 异步搜索该话题的热点
                hotspot_data = asyncio.run(_fetch_hotspots_for_subscription(sub.topic))

                if hotspot_data:
                    # 创建推送记录
                    push_record = subscription_service.create_push_record(
                        db=db,
                        subscription_id=sub.id,
                        topic=sub.topic,
                        hot_topic_data={'hotspots': hotspot_data}
                    )

                    # 更新订阅推送时间
                    subscription_service.update_subscription_push_time(db, sub.id)

                    logger.info(
                        f"推送成功: 用户={sub.user_id}, 话题={sub.topic}, "
                        f"热点数={len(hotspot_data)}, 推送记录ID={push_record.id}"
                    )
                else:
                    logger.warning(f"话题 {sub.topic} 未找到热点，跳过推送")

            except Exception as e:
                logger.error(f"推送订阅失败: sub_id={sub.id}, topic={sub.topic}, error={e}")
                # 单个订阅失败不影响其他订阅
                continue

        logger.info("推送任务完成")

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
    # 每天早上8点执行推送任务
    scheduler.add_job(
        scheduled_subscription_push,
        'cron',
        hour=8,
        minute=0,
        id='subscription_push',
        replace_existing=True,
    )
    logger.info("订阅推送任务已调度：每天 08:00 执行")

    # 可选：每3天也执行一次（用于 every_3_days 频率的订阅）
    # 由于已经通过 next_push_at 控制频率，这个主任务可以覆盖所有情况


# 用于测试的立即执行函数
def test_push_immediately():
    """测试：立即执行推送任务"""
    logger.info("执行测试推送任务...")
    scheduled_subscription_push()