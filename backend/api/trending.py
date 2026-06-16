"""
热点搜索路由
使用统一的 API 响应模型
"""
import logging

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from backend.models.schemas.request import TrendingSearchRequest
from backend.models.schemas.response import HotTopicResponse
from backend.models.schemas.api_response import ErrorCode
from backend.utils.api_response import (
    success_response,
    collection_response,
    paginated_response,
    error_response
)
from backend.services.trending_service import TrendingService
from backend.services.content_library_service import content_library_service
from backend.config.database import get_db
from backend.core.ai_service import ai_manager
from backend.models.database.tables import UserTable
from backend.config.settings import settings, ensure_dev_user
from backend.services.auth_service import auth_service
from backend.services.import_export_service import import_export_service

router = APIRouter(prefix="/trending", tags=["热点搜索"])

# 初始化服务
trending_service = TrendingService()


class ArticleContentRequest(BaseModel):
    """文章内容请求"""
    url: str
    source: str


class SummaryRequest(BaseModel):
    """热点总结请求"""
    title: str
    summary: str
    url: str
    source: str


@router.post("/search")
async def search_trending(
    request: TrendingSearchRequest,
    db: Session = Depends(get_db)
):
    """
    搜索热点话题

    使用统一的响应模型和错误处理
    """
    # 开发模式：直接返回默认用户
    user = ensure_dev_user(db)

    # 检查配额
    if not auth_service.check_quota(db, user.id, "search_trending"):
        return error_response(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"配额不足，当前余额: {user.quota_balance}",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    try:
        platforms = [p.value for p in request.platforms]
        logger.info(f"Starting trending search: keyword={request.keyword}, platforms={platforms}, days={request.days}")

        result = await trending_service.search(
            keyword=request.keyword,
            platforms=platforms,
            days=request.days
        )

        logger.info(f"Search result type: {type(result)}")
        logger.info(f"Search result: {result}")

        # 保存热点趋势数据
        try:
            trends_data = []
            for topic in result.hot_topics:
                trends_data.append({
                    "hot_topic_id": topic.id,
                    "hot_topic_title": topic.title,
                    "hot_topic_source": topic.source,
                    "heat_score": topic.heat_score,
                    "trend_direction": topic.trend_direction.value if hasattr(topic.trend_direction, 'value') else topic.trend_direction
                })
            if trends_data:
                content_library_service.batch_save_hot_topic_trends(db, trends_data)
                logger.info(f"已保存 {len(trends_data)} 条热点趋势数据")
        except Exception as e:
            # 趋势数据保存失败不影响搜索结果，只记录日志
            logger.warning(f"保存热点趋势数据失败: {e}")

        # 扣减配额
        logger.info("Deducting quota...")
        auth_service.deduct_quota(db, user.id, "search_trending")
        logger.info("Quota deducted successfully")

        logger.info("Creating success response...")
        logger.info(f"result.hot_topics type: {type(result.hot_topics)}")
        logger.info(f"len(result.hot_topics): {len(result.hot_topics)}")
        message = f"搜索到 {len(result.hot_topics)} 个热点话题"
        logger.info(f"Message: {message}")

        response = success_response(
            data=result,
            message=message
        )
        logger.info(f"Response created: {type(response)}")
        logger.info("About to return response...")
        return response
    except Exception as e:
        return error_response(
            code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message=f"搜索失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/summary")
async def get_topic_summary(request: SummaryRequest, db: Session = Depends(get_db)):
    """
    生成热点话题的AI总结

    返回热点事件的背景、关键事实、影响分析等内容
    """
    # 开发模式：直接返回默认用户
    user = ensure_dev_user(db)

    # 检查配额
    if not auth_service.check_quota(db, user.id, "ai_summary"):
        return error_response(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"配额不足，当前余额: {user.quota_balance}",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    try:
        prompt = f"""请对以下热点话题进行详细分析介绍，生成适合用于文案创作的内容摘要。

【标题】{request.title}
【来源】{request.source}
【简介】{request.summary}

请按照以下结构生成（使用markdown格式）：

# {request.title}

## 事件背景
（简述事件背景和起因）

## 核心事实
- 事实1
- 事实2
- 事实3

## 影响与分析
（分析事件的影响和意义）

## 观点与争议
（不同观点和争议点）

## 延伸话题
（可以延伸讨论的相关话题）

要求：
- 内容客观准确
- 结构清晰易读
- 总字数在500-800字之间
- 避免使用"本文""文章"等引用词
"""

        ai_content = ""
        if ai_manager.is_available():
            try:
                ai_content = await ai_manager.generate(prompt, max_tokens=1500)
            except Exception as e:
                logger.warning(f"AI生成失败: {e}")

        if not ai_content:
            # 回退到基础摘要
            ai_content = f"""# {request.title}

## 事件简介
{request.summary}

## 来源信息
- 来源: {request.source}
- 原文链接: {request.url}

## 延伸思考
这是一个值得关注的热点话题，建议进一步了解相关背景信息。
"""

        # 扣减配额
        auth_service.deduct_quota(db, user.id, "ai_summary")

        return success_response(
            data={
                "summary": ai_content,
                "title": request.title,
                "source": request.source,
                "url": request.url
            },
            message="生成总结成功"
        )

    except Exception as e:
        logger.error(f"生成总结失败: {e}")
        return error_response(
            code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message=f"生成总结失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/article/content")
async def get_article_content(request: ArticleContentRequest):
    """
    获取文章全文内容

    Args:
        request: 包含 url 和 source 的请求

    Returns:
        文章内容
    """
    try:
        content = ""

        if request.source == "百度新闻" or request.source == "百度热搜":
            from scrapers.baidu_news import BaiduNewsScraper
            scraper = BaiduNewsScraper()
            content = await scraper.get_article_content(request.url)
            await scraper.close()
        elif request.source == "微博热搜":
            from scrapers.weibo import WeiboScraper
            scraper = WeiboScraper()
            # 微博内容获取需要登录，这里返回链接
            content = f"请前往原链接查看完整内容：{request.url}"
            await scraper.close()
        elif request.source == "知乎热榜":
            from scrapers.zhihu import ZhihuScraper
            scraper = ZhihuScraper()
            # 知乎内容获取需要登录，这里返回链接
            content = f"请前往原链接查看完整内容：{request.url}"
            await scraper.close()
        elif request.source == "抖音热榜":
            from scrapers.douyin import DouyinScraper
            scraper = DouyinScraper()
            # 抖音内容获取需要特殊处理，这里返回链接
            content = f"请前往原链接查看完整内容：{request.url}"
            await scraper.close()
        elif request.source == "小红书":
            from scrapers.xiaohongshu import XiaohongshuScraper
            scraper = XiaohongshuScraper()
            # 小红书内容获取需要登录，这里返回链接
            content = f"请前往原链接查看完整内容：{request.url}"
            await scraper.close()
        else:
            # 默认返回链接
            content = f"请前往原链接查看完整内容：{request.url}"

        return success_response(
            data={"content": content, "url": request.url},
            message="获取成功"
        )

    except Exception as e:
        logger.error(f"获取文章内容失败: {e}")
        return error_response(
            code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message=f"获取文章内容失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/export")
async def export_trending(
    keyword: str = Query(..., description="搜索关键词"),
    format: str = Query("csv", pattern="^(csv|xlsx)$", description="导出格式"),
    db: Session = Depends(get_db)
):
    """
    导出热点搜索结果为 CSV 或 Excel

    不消耗配额（分析功能）
    """
    try:
        # 执行搜索（不扣减配额）
        platforms = ["douyin", "weibo", "xiaohongshu"]
        result = await trending_service.search(
            keyword=keyword,
            platforms=platforms,
            days=7
        )

        # 获取话题列表
        topics = result.hot_topics

        # 导出
        file_content = import_export_service.export_hot_topics(topics, format)

        if format == "csv":
            media_type = "text/csv"
            filename = f"hot_topics_{keyword}.csv"
        else:
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"hot_topics_{keyword}.xlsx"

        return Response(
            content=file_content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "export_error", "message": str(e)})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "server_error", "message": f"导出失败: {str(e)}"}
        )


@router.get("/platforms")
async def get_supported_platforms():
    """
    获取支持的平台列表
    """
    return success_response(
        data={
            "platforms": [
                {"value": "baidu", "name": "百度新闻", "enabled": True},
                {"value": "weibo", "name": "微博热搜", "enabled": True},
                {"value": "zhihu", "name": "知乎热榜", "enabled": True},
                {"value": "douyin", "name": "抖音热榜", "enabled": True},
                {"value": "xiaohongshu", "name": "小红书", "enabled": True},
            ]
        },
        message="获取支持的平台列表"
    )


@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return success_response(data={"status": "ok"}, message="热点搜索服务正常")
