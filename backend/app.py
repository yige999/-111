import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from scrapers import fetch_all_feeds, fetch_reddit_tools, fetch_hackernews_tools
from analyzers import GPTAnalyzer
from database import db
from models import RawTool, Tool, AnalysisLog

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("AutoSaaS Radar 后端启动")
    yield
    # 关闭时执行
    logger.info("AutoSaaS Radar 后端关闭")


# 创建FastAPI应用
app = FastAPI(
    title="AutoSaaS Radar API",
    description="全自动 AI SaaS 趋势雷达 API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 响应模型
class ToolsResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    count: int


class StatsResponse(BaseModel):
    success: bool
    data: Dict[str, Any]


class RefreshResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any] = {}


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# 获取最新工具
@app.get("/api/tools/latest", response_model=ToolsResponse)
async def get_latest_tools(limit: int = 50):
    """获取最新工具"""
    try:
        tools = await db.get_latest_tools(limit)
        return ToolsResponse(success=True, data=tools, count=len(tools))
    except Exception as e:
        logger.error(f"获取最新工具失败: {e}")
        raise HTTPException(status_code=500, detail="获取最新工具失败")


# 按分类获取工具
@app.get("/api/tools/category/{category}", response_model=ToolsResponse)
async def get_tools_by_category(category: str, limit: int = 50):
    """按分类获取工具"""
    try:
        tools = await db.get_tools_by_category(category, limit)
        return ToolsResponse(success=True, data=tools, count=len(tools))
    except Exception as e:
        logger.error(f"按分类获取工具失败: {e}")
        raise HTTPException(status_code=500, detail="按分类获取工具失败")


# 获取趋势工具
@app.get("/api/tools/trending", response_model=ToolsResponse)
async def get_trending_tools(days: int = 7, limit: int = 50):
    """获取趋势工具"""
    try:
        tools = await db.get_trending_tools(days, limit)
        return ToolsResponse(success=True, data=tools, count=len(tools))
    except Exception as e:
        logger.error(f"获取趋势工具失败: {e}")
        raise HTTPException(status_code=500, detail="获取趋势工具失败")


# 按日期获取工具
@app.get("/api/tools/date/{date}", response_model=ToolsResponse)
async def get_tools_by_date(date: str, limit: int = 50):
    """按日期获取工具"""
    try:
        tools = await db.get_tools_by_date(date, limit)
        return ToolsResponse(success=True, data=tools, count=len(tools))
    except Exception as e:
        logger.error(f"按日期获取工具失败: {e}")
        raise HTTPException(status_code=500, detail="按日期获取工具失败")


# 获取所有分类
@app.get("/api/categories")
async def get_categories():
    """获取所有分类"""
    try:
        categories = await db.get_categories()
        return {"success": True, "data": categories}
    except Exception as e:
        logger.error(f"获取分类失败: {e}")
        raise HTTPException(status_code=500, detail="获取分类失败")


# 获取统计信息
@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """获取统计信息"""
    try:
        stats = await db.get_stats()
        return StatsResponse(success=True, data=stats)
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")


# 手动刷新数据
@app.post("/api/tools/refresh", response_model=RefreshResponse)
async def refresh_tools(background_tasks: BackgroundTasks):
    """手动刷新数据"""
    try:
        # 添加后台任务
        background_tasks.add_task(refresh_tools_task)
        return RefreshResponse(
            success=True,
            message="数据刷新任务已启动，请稍后查看结果"
        )
    except Exception as e:
        logger.error(f"启动刷新任务失败: {e}")
        raise HTTPException(status_code=500, detail="启动刷新任务失败")


async def refresh_tools_task():
    """刷新工具数据的后台任务"""
    start_time = datetime.now()
    logger.info("开始执行数据刷新任务")

    try:
        # 1. 抓取数据
        logger.info("开始抓取RSS feeds...")
        rss_tools = await fetch_all_feeds(settings.rss_feeds_list)

        logger.info("开始抓取Reddit...")
        reddit_subreddits = ["SaaS", "SideProject", "Entrepreneur"]
        reddit_tools = await fetch_reddit_tools(
            reddit_subreddits,
            settings.reddit_client_id,
            settings.reddit_client_secret
        )

        logger.info("开始抓取Hacker News...")
        hn_tools = await fetch_hackernews_tools(25)

        # 合并所有工具
        all_raw_tools = rss_tools + reddit_tools + hn_tools
        logger.info(f"总共抓取到 {len(all_raw_tools)} 个原始工具")

        # 去重
        unique_tools = []
        seen_links = set()
        for tool in all_raw_tools:
            if tool.link not in seen_links:
                seen_links.add(tool.link)
                unique_tools.append(tool)

        logger.info(f"去重后有 {len(unique_tools)} 个唯一工具")

        # 2. AI分析
        if unique_tools:
            logger.info("开始AI分析...")
            analyzer = GPTAnalyzer()
            analysis_result = await analyzer.analyze_batch(unique_tools)

            if analysis_result["status"] == "success":
                analyzed_tools = analysis_result["analyzed_tools"]
                logger.info(f"AI分析完成，分析了 {len(analyzed_tools)} 个工具")

                # 3. 存储到数据库
                logger.info("开始存储到数据库...")
                success = await db.insert_tools(analyzed_tools)
                if success:
                    logger.info("数据存储成功")
                else:
                    logger.error("数据存储失败")

                # 4. 记录分析日志
                analysis_log = AnalysisLog(
                    date=start_time,
                    tools_analyzed=analysis_result["tools_count"],
                    tokens_used=analysis_result["tokens_used"],
                    cost_usd=analysis_result["cost_usd"],
                    status="success" if success else "failed"
                )
                await db.insert_analysis_log(analysis_log)

            else:
                logger.error(f"AI分析失败: {analysis_result.get('error', '未知错误')}")
        else:
            logger.info("没有新工具需要分析")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"数据刷新任务完成，耗时 {duration:.2f} 秒")

    except Exception as e:
        logger.error(f"数据刷新任务失败: {e}")

        # 记录失败日志
        try:
            analysis_log = AnalysisLog(
                date=start_time,
                tools_analyzed=0,
                tokens_used=0,
                cost_usd=0,
                status="failed",
                error_message=str(e)
            )
            await db.insert_analysis_log(analysis_log)
        except:
            pass  # 日志记录失败不影响主流程


# 根路径
@app.get("/")
async def root():
    """根路径信息"""
    return {
        "name": "AutoSaaS Radar API",
        "version": "1.0.0",
        "description": "全自动 AI SaaS 趋势雷达 API",
        "endpoints": {
            "health": "/health",
            "latest_tools": "/api/tools/latest",
            "tools_by_category": "/api/tools/category/{category}",
            "trending_tools": "/api/tools/trending",
            "tools_by_date": "/api/tools/date/{date}",
            "categories": "/api/categories",
            "stats": "/api/stats",
            "refresh": "/api/tools/refresh"
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )