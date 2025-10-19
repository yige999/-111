import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import tools, health
from app.api.dependencies import set_dependencies
from app.api.exceptions import setup_exception_handlers
from app.api.middleware import setup_middleware
from app.services.data_collector import DataCollector
from app.services.gpt_analyzer import GPTAnalyzer
from app.database.connection import DatabaseManager

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

# 全局变量
data_collector = None
gpt_analyzer = None
db_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global data_collector, gpt_analyzer, db_manager

    # 启动时初始化
    logger.info("正在启动 AutoSaaS Radar 后端服务...")

    try:
        # 初始化数据库连接
        db_manager = DatabaseManager()
        await db_manager.initialize()
        logger.info("数据库连接初始化完成")

        # 初始化数据收集器
        data_collector = DataCollector()
        logger.info("数据收集器初始化完成")

        # 初始化GPT分析器
        gpt_analyzer = GPTAnalyzer()
        logger.info("GPT分析器初始化完成")

        # 设置依赖注入
        set_dependencies(db_manager, data_collector, gpt_analyzer)

        # 存储到应用状态
        app.state.data_collector = data_collector
        app.state.gpt_analyzer = gpt_analyzer
        app.state.db_manager = db_manager

        logger.info("AutoSaaS Radar 后端服务启动成功!")

        yield

    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        raise
    finally:
        # 关闭时清理
        logger.info("正在关闭服务...")
        if db_manager:
            await db_manager.close()
        logger.info("服务已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="AutoSaaS Radar API",
    description="全自动 AI SaaS 趋势雷达后端API",
    version="1.0.0",
    lifespan=lifespan
)

# 设置异常处理器
setup_exception_handlers(app)

# 设置中间件
setup_middleware(app)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router, prefix="/api", tags=["健康检查"])
app.include_router(tools.router, prefix="/api/tools", tags=["工具数据"])

# 静态文件（如果需要）
# app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AutoSaaS Radar API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )