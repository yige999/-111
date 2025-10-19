"""
健康检查API路由
提供服务状态监控和健康检查接口
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.dependencies import DatabaseDep, DataCollectorDep, GPTAnalyzerDep
from utils.logger import logger

router = APIRouter()


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: str
    service: str
    version: str
    components: Dict[str, Dict[str, Any]]


class ComponentStatus(BaseModel):
    """组件状态"""
    status: str  # "healthy", "unhealthy", "degraded"
    message: str
    last_check: str
    response_time_ms: float = 0.0


@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: DatabaseDep,
    data_collector: DataCollectorDep,
    gpt_analyzer: GPTAnalyzerDep
):
    """
    全面健康检查
    - 检查数据库连接
    - 检查数据收集器状态
    - 检查GPT分析器状态
    - 返回系统整体状态
    """
    start_time = datetime.utcnow()
    components = {}
    overall_status = "healthy"

    # 检查数据库连接
    try:
        db_start = datetime.utcnow()
        db_status = await db.health_check()
        db_response_time = (datetime.utcnow() - db_start).total_seconds() * 1000

        components["database"] = ComponentStatus(
            status="healthy" if db_status else "unhealthy",
            message="数据库连接正常" if db_status else "数据库连接失败",
            last_check=datetime.utcnow().isoformat(),
            response_time_ms=db_response_time
        ).dict()

        if not db_status:
            overall_status = "unhealthy"

    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        components["database"] = ComponentStatus(
            status="unhealthy",
            message=f"数据库检查异常: {str(e)}",
            last_check=datetime.utcnow().isoformat()
        ).dict()
        overall_status = "unhealthy"

    # 检查数据收集器
    try:
        collector_start = datetime.utcnow()
        collector_status = await data_collector.health_check()
        collector_response_time = (datetime.utcnow() - collector_start).total_seconds() * 1000

        components["data_collector"] = ComponentStatus(
            status="healthy" if collector_status else "degraded",
            message="数据收集器正常" if collector_status else "数据收集器异常",
            last_check=datetime.utcnow().isoformat(),
            response_time_ms=collector_response_time
        ).dict()

        if not collector_status and overall_status == "healthy":
            overall_status = "degraded"

    except Exception as e:
        logger.error(f"数据收集器健康检查失败: {e}")
        components["data_collector"] = ComponentStatus(
            status="unhealthy",
            message=f"数据收集器检查异常: {str(e)}",
            last_check=datetime.utcnow().isoformat()
        ).dict()
        overall_status = "unhealthy"

    # 检查GPT分析器
    try:
        analyzer_start = datetime.utcnow()
        analyzer_status = await gpt_analyzer.health_check()
        analyzer_response_time = (datetime.utcnow() - analyzer_start).total_seconds() * 1000

        components["gpt_analyzer"] = ComponentStatus(
            status="healthy" if analyzer_status else "degraded",
            message="GPT分析器正常" if analyzer_status else "GPT分析器异常",
            last_check=datetime.utcnow().isoformat(),
            response_time_ms=analyzer_response_time
        ).dict()

        if not analyzer_status and overall_status == "healthy":
            overall_status = "degraded"

    except Exception as e:
        logger.error(f"GPT分析器健康检查失败: {e}")
        components["gpt_analyzer"] = ComponentStatus(
            status="unhealthy",
            message=f"GPT分析器检查异常: {str(e)}",
            last_check=datetime.utcnow().isoformat()
        ).dict()
        overall_status = "unhealthy"

    total_response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

    health_response = HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        service="AutoSaaS Radar API",
        version="1.0.0",
        components=components
    )

    logger.info(f"健康检查完成，状态: {overall_status}, 响应时间: {total_response_time:.2f}ms")
    return health_response


@router.get("/health/simple")
async def simple_health_check():
    """
    简单健康检查
    - 仅返回服务状态
    - 适用于负载均衡器探针
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "AutoSaaS Radar API"
    }


@router.get("/ready")
async def readiness_check(
    db: DatabaseDep
):
    """
    就绪检查
    - 检查服务是否准备好接收请求
    - 主要检查数据库连接
    """
    try:
        # 检查数据库连接
        db_healthy = await db.health_check()

        if not db_healthy:
            raise HTTPException(status_code=503, detail="服务未就绪")

        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "服务已就绪"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"就绪检查失败: {e}")
        raise HTTPException(status_code=503, detail="服务未就绪")


@router.get("/live")
async def liveness_check():
    """
    存活检查
    - 检查服务是否存活
    - 总是返回成功（除非服务完全崩溃）
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "服务正在运行"
    }


@router.get("/metrics")
async def get_metrics(
    db: DatabaseDep
):
    """
    获取服务指标
    - 数据库连接数
    - 最后更新时间
    - 错误统计
    """
    try:
        metrics = await db.get_metrics()

        # 添加基础指标
        metrics.update({
            "service": "AutoSaaS Radar API",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": 0,  # 这里可以实现实际运行时间计算
        })

        return metrics

    except Exception as e:
        logger.error(f"获取指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取指标失败")


@router.get("/version")
async def get_version():
    """
    获取服务版本信息
    """
    return {
        "service": "AutoSaaS Radar API",
        "version": "1.0.0",
        "build_time": "2024-01-15T00:00:00Z",  # 可以从环境变量获取
        "python_version": "3.x",
        "fastapi_version": "0.x",
        "timestamp": datetime.utcnow().isoformat()
    }