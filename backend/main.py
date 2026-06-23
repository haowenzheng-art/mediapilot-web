"""
MediaPilot 后端API服务入口
"""
import sys
import os
import asyncio
import logging
import time
from logging.handlers import TimedRotatingFileHandler

# 导入 settings（pydantic-settings 自动加载 .env）
from backend.config.settings import settings

# 配置日志系统：按日切割 + 保留 N 天，避免 backend.log 无限增长
os.makedirs("logs", exist_ok=True)
_log_handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
try:
    _rot = TimedRotatingFileHandler(
        filename="logs/backend.log",
        when="midnight",
        backupCount=settings.LOG_RETENTION_DAYS,
        encoding="utf-8",
        utc=False,
    )
    _rot.suffix = "%Y-%m-%d"
    _log_handlers.append(_rot)
except Exception as _e:
    # 日志目录不可写也不应阻塞启动
    print(f"[main] rotating log handler init failed: {_e}", file=sys.stderr)

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=_log_handlers,
)
logger = logging.getLogger(__name__)

# Sentry：仅当配置了 DSN 时启用，避免 dev 误上报
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            integrations=[StarletteIntegration(), FastApiIntegration()],
            send_default_pii=False,
        )
        logger.info(f"Sentry 已启用: env={settings.SENTRY_ENVIRONMENT}")
    except Exception as e:
        logger.warning(f"Sentry 初始化失败（不影响启动）: {e}")

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from apscheduler.schedulers.background import BackgroundScheduler

# 导入统一错误处理
from backend.utils.exceptions_typed import DatabaseError
from backend.utils.api_response import error_response

# 导入路由注册函数
from backend.api import register_routes

# 导入数据库配置
from backend.config.database import init_db, SessionLocal

# 导入AI服务
from backend.core.ai_service import ai_manager

# 导入转写引擎
from backend.core.transcribe_engine import TranscribeEngineManager

# 导入令牌清理服务
from backend.services.token_cleanup_service import token_cleanup_service

# 导入订阅推送服务
from backend.services.subscription_scheduler_service import schedule_push_tasks

# 全局转写引擎实例
transcribe_engine = None

# ARQ Redis 连接池
arq_pool = None
# 重连锁 + 退避（防止 Redis 真挂时并发请求刷爆日志）
_arq_reconnect_lock = asyncio.Lock()
_arq_last_fail_ts: float = 0.0
_ARQ_RECONNECT_BACKOFF = 3.0  # 失败后 3s 内不再尝试重连


async def get_arq_pool():
    """获取 ARQ Redis 连接池，None 时尝试 lazy 重连。

    生产场景：Redis 短暂网络抖动恢复后，startup 时建立的 pool 已是 None，
    请求路径调用本函数即可触发重连，无需重启 backend。
    """
    global arq_pool, _arq_last_fail_ts
    if arq_pool is not None:
        return arq_pool

    # 失败退避：上次失败后 _ARQ_RECONNECT_BACKOFF 秒内直接放弃
    now = time.monotonic()
    if now - _arq_last_fail_ts < _ARQ_RECONNECT_BACKOFF:
        return None

    async with _arq_reconnect_lock:
        if arq_pool is not None:  # double-check after lock
            return arq_pool
        try:
            from arq.connections import RedisSettings, create_pool
            from backend.worker import _parse_redis_url
            kwargs = _parse_redis_url(settings.REDIS_URL) or {"host": "localhost", "port": 6379, "database": 0}
            arq_pool = await create_pool(RedisSettings(**kwargs))
            await arq_pool.ping()
            logger.info(f"ARQ Redis lazy 重连成功: {settings.REDIS_URL}")
            _arq_last_fail_ts = 0.0
            return arq_pool
        except Exception as e:
            _arq_last_fail_ts = time.monotonic()
            logger.warning(f"ARQ Redis lazy 重连失败: {e}，{_ARQ_RECONNECT_BACKOFF}s 后再试")
            arq_pool = None
            return None

# APScheduler 实例
scheduler = BackgroundScheduler()


def scheduled_token_cleanup():
    """定时任务：清理过期和撤销的令牌"""
    db = SessionLocal()
    try:
        token_cleanup_service.cleanup_expired_and_revoked(db)
    except Exception as e:
        logger.error(f"定时令牌清理失败: {e}")
    finally:
        db.close()


app = FastAPI(
    title="MediaPilot API",
    version="1.0.0"
)

# 添加全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器
    记录所有未捕获的异常并返回统一错误响应
    """
    logger.error(f"未捕获的异常: {type(exc).__name__} - {str(exc)}", exc_info=True)

    return error_response(
        code="internal_error",
        message="服务器内部错误，请稍后重试",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"error_type": type(exc).__name__, "error_message": str(exc)}
    )


@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    """
    数据库异常处理器
    """
    logger.error(f"数据库错误: {str(exc)}", exc_info=True)

    return error_response(
        code="database_error",
        message="数据库操作失败",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

# CORS 配置：开发模式允许 localhost 系列；生产必须显式列出
if settings.DEV_MODE:
    cors_origins = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
else:
    cors_origins = settings.cors_origins_list
    if not cors_origins:
        raise RuntimeError("生产环境必须配置 CORS_ORIGINS，不允许为空")

# 当 allow_credentials=True 时，allow_origins 不能为 ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# 请求 ID + 访问日志中间件
from backend.middleware.request_id import create_request_id_middleware
app.middleware("http")(create_request_id_middleware())

# 注册路由
register_routes(app, transcribe_engine)


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库和AI服务"""
    logger.info("MediaPilot 后端服务启动中...")

    try:
        init_db()
        logger.info("数据库初始化完成")
    except DatabaseError as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise
    else:
        # 不重新抛出异常，避免启动失败
        pass

    # 初始化AI服务
    from backend.config.settings import settings

    if settings.AI_API_KEY:
        ai_manager.configure(
            provider=settings.AI_PROVIDER,
            api_key=settings.AI_API_KEY,
            base_url=settings.AI_BASE_URL,
            model=settings.AI_MODEL,
            timeout=settings.AI_TIMEOUT,
            max_retries=settings.AI_MAX_RETRIES
        )
        if ai_manager.is_available():
            logger.info(f"AI服务已配置: {settings.AI_PROVIDER}/{settings.AI_MODEL}")
        else:
            logger.warning("AI服务配置但不可用")
    else:
        logger.warning("未配置AI_API_KEY，内容生成将使用模拟数据")

    # 初始化转写引擎
    global transcribe_engine

    try:
        if settings.USE_MOCK_TRANSCRIBE:
            transcribe_engine = TranscribeEngineManager("mock", {})
            logger.info("转写引擎: mock 模式")
        else:
            engine_type = settings.TRANSCRIBE_ENGINE
            engine_config = {}

            if engine_type == "whisper_local":
                engine_config = {
                    "model": settings.WHISPER_MODEL or "base",
                    "language": settings.WHISPER_LANGUAGE or "zh"
                }
            elif engine_type == "aliyun":
                engine_config = {
                    "access_key_id": settings.ALIYUN_ACCESS_KEY_ID,
                    "access_key_secret": settings.ALIYUN_ACCESS_KEY_SECRET,
                    "app_key": settings.ALIYUN_APP_KEY
                }
            elif engine_type == "volcengine":
                engine_config = {
                    "access_key": settings.VOLCENGINE_ACCESS_KEY,
                    "secret_access_key": settings.VOLCENGINE_SECRET_ACCESS_KEY,
                    "app_key": settings.VOLCENGINE_APP_ID
                }

            transcribe_engine = TranscribeEngineManager(engine_type, engine_config)

            if transcribe_engine.is_available():
                logger.info(f"转写引擎已配置: {engine_type}")
            else:
                logger.warning(f"转写引擎 {engine_type} 不可用，回退到 mock 模式")
                transcribe_engine = TranscribeEngineManager("mock", {})
    except Exception as e:
        logger.warning(f"转写引擎初始化失败: {e}，使用mock模式")
        transcribe_engine = None

    # 将真实初始化好的转写引擎注入到 media 路由（register_routes 在模块加载时执行，
    # 那时 transcribe_engine 还是 None，必须在 startup 完成初始化后再注入一次）
    try:
        from backend.api.media import set_transcribe_engine
        set_transcribe_engine(transcribe_engine)
        logger.info(f"已将转写引擎注入 media 路由: {transcribe_engine.engine_type if transcribe_engine else 'None'}")
    except Exception as e:
        logger.warning(f"转写引擎注入 media 路由失败: {e}")

    # 初始化 ARQ Redis 连接池
    global arq_pool
    try:
        from arq.connections import RedisSettings, create_pool
        from backend.worker import _parse_redis_url
        kwargs = _parse_redis_url(settings.REDIS_URL) or {"host": "localhost", "port": 6379, "database": 0}
        arq_pool = await create_pool(RedisSettings(**kwargs))
        logger.info(f"ARQ Redis 连接成功: {settings.REDIS_URL}")
    except Exception as e:
        logger.warning(f"ARQ Redis 连接失败: {e}，任务队列不可用")
        arq_pool = None

    # 启动定时任务
    if not scheduler.running:
        # 每天凌晨2:03清理过期令牌
        scheduler.add_job(
            scheduled_token_cleanup,
            'cron',
            hour=2,
            minute=3,
            id='token_cleanup',
            replace_existing=True,
        )

        # 订阅推送任务
        schedule_push_tasks(scheduler)

        scheduler.start()
        logger.info("APScheduler 已启动: 令牌清理(02:03) + 订阅推送(08:00)")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时释放所有资源：调度器、Redis 连接池、数据库连接池"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler 已停止")

    global arq_pool
    if arq_pool is not None:
        try:
            await arq_pool.close()
            logger.info("ARQ Redis 连接池已关闭")
        except Exception as e:
            logger.error(f"ARQ Redis 连接池关闭失败: {e}")
        finally:
            arq_pool = None

    from backend.config.database import dispose_engine
    dispose_engine()

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "MediaPilot API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查：真实探测 DB 与 Redis 连通性"""
    db_ok = False
    redis_ok = False
    try:
        from backend.config.database import SessionLocal
        db = SessionLocal()
        try:
            db.execute(__import__("sqlalchemy").text("SELECT 1"))
            db_ok = True
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"健康检查 DB 探测失败: {e}")

    if arq_pool is not None:
        try:
            await arq_pool.ping()
            redis_ok = True
        except Exception as e:
            logger.warning(f"健康检查 Redis 探测失败: {e}")

    all_ok = db_ok and redis_ok
    return {
        "status": "healthy" if all_ok else "degraded",
        "version": "1.0.0",
        "services": {
            "api": "running",
            "database": "connected" if db_ok else "disconnected",
            "redis": "connected" if redis_ok else "disconnected",
            "ai_service": ai_manager.is_available(),
            "transcribe_engine": transcribe_engine.engine_type if transcribe_engine else None,
        },
    }


@app.get("/queue/health")
async def queue_health():
    """ARQ 队列健康：Redis ping + 注册的 worker functions 数量"""
    pool = await get_arq_pool()
    if pool is None:
        return {"status": "down", "redis": "disconnected", "reason": "ARQ pool unavailable"}
    try:
        await pool.ping()
    except Exception as e:
        logger.warning(f"queue health redis ping 失败: {e}")
        return {"status": "down", "redis": "ping_failed", "error": str(e)}

    from backend.worker import Worker as _W
    fns = [getattr(f, "__name__", str(f)) for f in (_W.functions or [])]
    return {
        "status": "ok",
        "redis": "connected",
        "registered_functions": fns,
        "max_jobs": _W.max_jobs,
        "job_timeout": _W.job_timeout,
    }


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
