"""
工具数据API路由
提供AI工具数据的查询和管理接口
"""

from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from app.api.dependencies import DatabaseDep, DataCollectorDep, GPTAnalyzerDep
from app.models.tool import Tool, ToolCreate, ToolResponse
from utils.logger import logger

router = APIRouter()


class TrendingRequest(BaseModel):
    """趋势请求参数"""
    days: int = Field(default=7, description="统计天数", ge=1, le=30)
    category: Optional[str] = Field(default=None, description="筛选分类")


class RefreshResponse(BaseModel):
    """数据刷新响应"""
    success: bool
    message: str
    tools_collected: int = 0
    tools_analyzed: int = 0
    duration_seconds: float = 0.0


@router.get("/latest", response_model=List[ToolResponse])
async def get_latest_tools(
    limit: int = Query(default=10, le=100, description="返回数量限制"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    db: DatabaseDep
):
    """
    获取最新AI工具数据
    - 按时间倒序排列
    - 支持分页
    """
    try:
        tools = await db.get_latest_tools(limit=limit, offset=offset)
        logger.info(f"获取最新工具成功，返回{len(tools)}条记录")
        return tools
    except Exception as e:
        logger.error(f"获取最新工具失败: {e}")
        raise HTTPException(status_code=500, detail="获取最新工具失败")


@router.get("/category/{category}", response_model=List[ToolResponse])
async def get_tools_by_category(
    category: str,
    limit: int = Query(default=20, le=100, description="返回数量限制"),
    days: int = Query(default=30, le=365, description="统计天数"),
    db: DatabaseDep
):
    """
    按分类获取AI工具
    - 按投票数倒序排列
    - 支持时间范围筛选
    """
    try:
        # 验证分类有效性
        valid_categories = ["Video", "Text", "Productivity", "Marketing", "Education", "Audio", "Other"]
        if category not in valid_categories:
            raise HTTPException(status_code=400, detail=f"无效的分类，支持的分类: {', '.join(valid_categories)}")

        start_date = datetime.utcnow() - timedelta(days=days)
        tools = await db.get_tools_by_category(category, start_date, limit)

        logger.info(f"获取分类工具成功，分类: {category}, 返回{len(tools)}条记录")
        return tools
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分类工具失败: {e}")
        raise HTTPException(status_code=500, detail="获取分类工具失败")


@router.get("/trending", response_model=List[ToolResponse])
async def get_trending_tools(
    days: int = Query(default=7, le=30, description="统计天数"),
    category: Optional[str] = Query(default=None, description="筛选分类"),
    min_votes: int = Query(default=10, ge=0, description="最小投票数"),
    limit: int = Query(default=20, le=100, description="返回数量限制"),
    db: DatabaseDep
):
    """
    获取趋势工具
    - 筛选上升趋势的工具
    - 按投票数和趋势信号排序
    - 支持分类筛选
    """
    try:
        if days < 1 or days > 30:
            raise HTTPException(status_code=400, detail="天数必须在1-30之间")

        start_date = datetime.utcnow() - timedelta(days=days)

        # 验证分类（如果提供）
        if category:
            valid_categories = ["Video", "Text", "Productivity", "Marketing", "Education", "Audio", "Other"]
            if category not in valid_categories:
                raise HTTPException(status_code=400, detail=f"无效的分类")

        tools = await db.get_trending_tools(
            start_date=start_date,
            category=category,
            min_votes=min_votes,
            limit=limit
        )

        logger.info(f"获取趋势工具成功，天数: {days}, 分类: {category or '全部'}, 返回{len(tools)}条记录")
        return tools
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取趋势工具失败: {e}")
        raise HTTPException(status_code=500, detail="获取趋势工具失败")


@router.get("/date/{target_date}", response_model=List[ToolResponse])
async def get_tools_by_date(
    target_date: date,
    db: DatabaseDep
):
    """
    按日期获取AI工具
    - 返回指定日期的所有工具
    - 按投票数倒序排列
    """
    try:
        # 验证日期不能是未来
        if target_date > date.today():
            raise HTTPException(status_code=400, detail="查询日期不能是未来时间")

        # 限制查询范围（最多查询365天前）
        min_date = date.today() - timedelta(days=365)
        if target_date < min_date:
            raise HTTPException(status_code=400, detail="查询日期不能超过365天前")

        tools = await db.get_tools_by_date(target_date)

        logger.info(f"按日期获取工具成功，日期: {target_date}, 返回{len(tools)}条记录")
        return tools
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"按日期获取工具失败: {e}")
        raise HTTPException(status_code=500, detail="按日期获取工具失败")


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_tools_data(
    background_tasks: BackgroundTasks,
    force: bool = Query(default=False, description="强制刷新，忽略时间限制"),
    db: DatabaseDep,
    data_collector: DataCollectorDep,
    gpt_analyzer: GPTAnalyzerDep
):
    """
    手动刷新工具数据
    - 抓取最新数据
    - AI分析处理
    - 存储到数据库
    - 支持后台执行
    """
    try:
        # 检查是否有正在进行的刷新任务
        is_refreshing = await db.is_refreshing()
        if is_refreshing and not force:
            raise HTTPException(status_code=409, detail="数据刷新任务正在进行中")

        # 记录刷新开始
        await db.set_refreshing_status(True)
        start_time = datetime.utcnow()

        # 添加后台任务
        background_tasks.add_task(
            refresh_data_background,
            db=db,
            data_collector=data_collector,
            gpt_analyzer=gpt_analyzer,
            start_time=start_time
        )

        logger.info("数据刷新任务已启动")
        return RefreshResponse(
            success=True,
            message="数据刷新任务已启动，正在后台执行"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动数据刷新失败: {e}")
        # 重置刷新状态
        await db.set_refreshing_status(False)
        raise HTTPException(status_code=500, detail="启动数据刷新失败")


async def refresh_data_background(
    db: DatabaseManager,
    data_collector: DataCollector,
    gpt_analyzer: GPTAnalyzer,
    start_time: datetime
):
    """后台刷新数据任务"""
    try:
        logger.info("开始执行后台数据刷新")

        # 1. 抓取原始数据
        raw_tools = await data_collector.collect_all_sources()
        logger.info(f"抓取到 {len(raw_tools)} 个原始工具")

        # 2. AI分析处理
        analyzed_tools = []
        for tool in raw_tools:
            try:
                analyzed = await gpt_analyzer.analyze_tool(tool)
                analyzed_tools.append(analyzed)
            except Exception as e:
                logger.error(f"AI分析工具失败: {tool.get('tool_name', 'Unknown')}, 错误: {e}")
                continue

        logger.info(f"AI分析完成，处理了 {len(analyzed_tools)} 个工具")

        # 3. 存储到数据库
        if analyzed_tools:
            await db.insert_tools_batch(analyzed_tools)
            logger.info(f"成功存储 {len(analyzed_tools)} 个工具到数据库")

        # 4. 记录分析日志
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        await db.log_analysis(
            tools_analyzed=len(analyzed_tools),
            duration_seconds=duration,
            status="success"
        )

        logger.info(f"后台数据刷新完成，耗时: {duration:.2f}秒")

    except Exception as e:
        logger.error(f"后台数据刷新失败: {e}")
        # 记录失败日志
        try:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            await db.log_analysis(
                tools_analyzed=0,
                duration_seconds=duration,
                status="failed",
                error_message=str(e)
            )
        except:
            pass
    finally:
        # 重置刷新状态
        await db.set_refreshing_status(False)


@router.get("/stats")
async def get_tools_stats(
    days: int = Query(default=7, le=30, description="统计天数"),
    db: DatabaseDep
):
    """
    获取工具统计信息
    - 分类统计
    - 趋势统计
    - 数量统计
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        stats = await db.get_tools_statistics(start_date)

        logger.info(f"获取工具统计成功，天数: {days}")
        return stats
    except Exception as e:
        logger.error(f"获取工具统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取工具统计失败")


@router.get("/search", response_model=List[ToolResponse])
async def search_tools(
    query: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    limit: int = Query(default=20, le=100, description="返回数量限制"),
    category: Optional[str] = Query(default=None, description="筛选分类"),
    db: DatabaseDep
):
    """
    搜索工具
    - 支持工具名称和描述搜索
    - 支持分类筛选
    - 按相关性排序
    """
    try:
        # 验证分类（如果提供）
        if category:
            valid_categories = ["Video", "Text", "Productivity", "Marketing", "Education", "Audio", "Other"]
            if category not in valid_categories:
                raise HTTPException(status_code=400, detail=f"无效的分类")

        tools = await db.search_tools(query, category, limit)

        logger.info(f"搜索工具成功，关键词: {query}, 分类: {category or '全部'}, 返回{len(tools)}条记录")
        return tools
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索工具失败: {e}")
        raise HTTPException(status_code=500, detail="搜索工具失败")