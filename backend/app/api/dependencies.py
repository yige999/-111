"""
API依赖注入
提供FastAPI路由所需的依赖项
"""

from typing import Annotated
from fastapi import Depends

from app.database.connection import DatabaseManager
from app.services.data_collector import DataCollector
from app.services.gpt_analyzer import GPTAnalyzer


# 全局依赖实例（这些在应用启动时初始化）
_db_manager: DatabaseManager = None
_data_collector: DataCollector = None
_gpt_analyzer: GPTAnalyzer = None


def set_dependencies(
    db_manager: DatabaseManager,
    data_collector: DataCollector,
    gpt_analyzer: GPTAnalyzer
):
    """设置全局依赖实例（在应用启动时调用）"""
    global _db_manager, _data_collector, _gpt_analyzer
    _db_manager = db_manager
    _data_collector = data_collector
    _gpt_analyzer = gpt_analyzer


async def get_database() -> DatabaseManager:
    """获取数据库管理器依赖"""
    if _db_manager is None:
        raise RuntimeError("数据库管理器未初始化")
    return _db_manager


async def get_data_collector() -> DataCollector:
    """获取数据收集器依赖"""
    if _data_collector is None:
        raise RuntimeError("数据收集器未初始化")
    return _data_collector


async def get_gpt_analyzer() -> GPTAnalyzer:
    """获取GPT分析器依赖"""
    if _gpt_analyzer is None:
        raise RuntimeError("GPT分析器未初始化")
    return _gpt_analyzer


# 类型别名
DatabaseDep = Annotated[DatabaseManager, Depends(get_database)]
DataCollectorDep = Annotated[DataCollector, Depends(get_data_collector)]
GPTAnalyzerDep = Annotated[GPTAnalyzer, Depends(get_gpt_analyzer)]