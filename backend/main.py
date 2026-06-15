"""
MediaPilot 后端API服务入口
"""
import sys
import os
import logging

# 加载环境变量
try:
    from dotenv import load_dotenv
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, ".env")
    load_dotenv(env_path)
except ImportError:
    pass

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

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

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    if os.getenv("AI_API_KEY"):
        ai_manager.configure(
            provider=os.getenv("AI_PROVIDER", "openai"),
            api_key=os.getenv("AI_API_KEY"),
            base_url=os.getenv("AI_BASE_URL"),
            model=os.getenv("AI_MODEL", "agnes-2.0-flash"),
            timeout=int(os.getenv("AI_TIMEOUT", "60")),
            max_retries=3
        )
        if ai_manager.is_available():
            logger.info(f"AI服务已配置: {os.getenv('AI_PROVIDER')}/{os.getenv('AI_MODEL')}")
        else:
            logger.warning("AI服务配置但不可用")
    else:
        logger.warning("未配置AI_API_KEY，内容生成将使用模拟数据")

    # 初始化转写引擎
    global transcribe_engine

    try:
        if os.getenv("USE_MOCK_TRANSCRIBE", "true").lower() == "true":
            transcribe_engine = TranscribeEngineManager("mock", {})
            logger.info("转写引擎: mock 模式")
        else:
            engine_type = os.getenv("TRANSCRIBE_ENGINE", "whisper_local")
            engine_config = {}

            if engine_type == "whisper_local":
                engine_config = {
                    "model": os.getenv("WHISPER_MODEL") or "base",
                    "language": os.getenv("WHISPER_LANGUAGE") or "zh"
                }
            elif engine_type == "aliyun":
                engine_config = {
                    "access_key_id": os.getenv("ALIYUN_ACCESS_KEY_ID", ""),
                    "access_key_secret": os.getenv("ALIYUN_ACCESS_KEY_SECRET", ""),
                    "app_key": os.getenv("ALIYUN_APP_KEY", "")
                }
            elif engine_type == "volcengine":
                engine_config = {
                    "access_key": os.getenv("VOLCENGINE_ACCESS_KEY", ""),
                    "secret_access_key": os.getenv("VOLCENGINE_SECRET_ACCESS_KEY", ""),
                    "app_key": os.getenv("VOLCENGINE_APP_ID", "")
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
    """应用关闭时停止调度器"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler 已停止")

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
    """健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "api": "running",
            "database": "connected",
            "ai_service": ai_manager.is_available(),
            "transcribe_engine": transcribe_engine.engine_type if transcribe_engine else None
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
