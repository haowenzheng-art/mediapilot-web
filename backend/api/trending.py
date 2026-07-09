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
from backend.api.dependencies import get_current_user

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
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    搜索热点话题

    使用统一的响应模型和错误处理
    """
    user = current_user

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
async def get_topic_summary(
    request: SummaryRequest,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    生成热点话题的AI总结（v2 契约）：

    - AI 不可用 / AI 失败 / AI 返回空 → 503 EXTERNAL_SERVICE_ERROR + 不扣配额 + 不返假数据
      （遵守 CLAUDE.md「数据真实性原则」—— 没有真实数据就如实降级，绝不用模板拼的假内容糊弄）
    - AI 成功 → 200 + 扣配额
    - 输出格式：5 段【】包裹的主题段落，口语化，适合直接改写成口播文案
      （遵守 CLAUDE.md「AI 内容格式规范」—— 不用 "#" 符号、避免"本文/文章"等套话）
    """
    user = current_user

    # 1) 配额前置检查
    if not auth_service.check_quota(db, user.id, "ai_summary"):
        return error_response(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"配额不足，当前余额 {user.quota_balance}",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    # 2) AI 可用性检查：未配置 / 不可用 → 503，不返假数据
    if not ai_manager.is_available():
        return error_response(
            code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message="AI 服务暂不可用，请稍后再试",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    # 3) prompt：去 # 字符 + 口语化 + 明确"作为口播文案素材"
    prompt = f"""请基于以下热点话题，写一段适合直接用于口播文案的素材笔记。

【标题】{request.title}
【来源】{request.source}
【原始简介】{request.summary}

要求：
- 输出 5 个段落，每段以【】包裹的主题词开头（如【背景】【核心事实】【影响】【观点】【延伸】）
- 每段 2-3 句，口语化，读者能直接拿来改写成口播文案
- 不要用 "#" 符号（任何井号开头都不行）
- 不要分点列示（不要写 "- " "1." 等枚举符）
- 不要用"本文""文章""综上所述""值得注意的是"等套话
- 控制在 500-700 字
- 客观准确，避免主观评价
"""

    # 4) 调 AI；失败/空 都返 503，绝不返假数据兜底
    try:
        ai_content = await ai_manager.generate(prompt, max_tokens=1500)
    except Exception as e:
        logger.warning(f"AI 总结失败: {e}")
        return error_response(
            code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message=f"AI 总结失败：{str(e)}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    if not ai_content or not ai_content.strip():
        logger.warning("AI 总结返回为空")
        return error_response(
            code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message="AI 总结返回为空，请重试",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    # 5) 成功后扣配额（失败路径已在 4 步 return，不再走到这里）
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

        if request.source in ("百度新闻", "百度热搜", "今日头条"):
            from backend.scrapers.baidu_news import BaiduNewsScraper
            scraper = BaiduNewsScraper()
            content = await scraper.get_article_content(request.url)
            await scraper.close()
        else:
            # v4 精简：不再为下线的微博/知乎/抖音/小红书 走专门爬虫分支
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
        # v4 精简：导出默认走 baidu + toutiao
        platforms = ["baidu", "toutiao"]
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
    获取支持的平台列�?
    """
    return success_response(
        data={
            "platforms": [
                {"value": "baidu", "name": "百度新闻", "enabled": True},
                {"value": "toutiao", "name": "今日头条", "enabled": True},
            ]
        },
        message="获取支持的平台列�?"
    )


@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return success_response(data={"status": "ok"}, message="热点搜索服务正常")
