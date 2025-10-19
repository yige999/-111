# Database Module - 数据存储模块
from .supabase_client import SupabaseDB, db
from .database_manager import DatabaseManager, db_manager
from .data_validator import DataValidator, data_validator, ValidationResult
from .batch_optimizer import BatchOptimizer, batch_optimizer

# 便捷导入
__all__ = [
    # 核心客户端
    'SupabaseDB', 'db',

    # 高级管理器
    'DatabaseManager', 'db_manager',

    # 数据验证
    'DataValidator', 'data_validator', 'ValidationResult',

    # 批量优化
    'BatchOptimizer', 'batch_optimizer',

    # 便捷接口
    'validate_tool', 'validate_batch',
    'insert_tools', 'get_latest_tools',
    'batch_insert', 'smart_insert'
]

# 便捷函数接口
async def validate_tool(tool_data: dict):
    """验证单个工具数据"""
    return await data_validator.validate_tool(tool_data)

async def validate_batch(tools_data: list):
    """批量验证工具数据"""
    return await data_validator.validate_batch(tools_data)

async def insert_tools(tools_data: list):
    """插入工具数据（带验证）"""
    return await db_manager.batch_insert_tools(tools_data)

async def get_latest_tools(limit: int = 50):
    """获取最新工具"""
    return await db_manager.db.get_latest_tools(limit)

async def batch_insert(tools_data: list, batch_size: int = 50):
    """批量插入工具（优化版）"""
    batch_optimizer.batch_size = batch_size
    return await batch_optimizer.smart_batch_insert(tools_data)

async def smart_insert(tools_data: list):
    """智能批量插入（自动优化）"""
    return await batch_optimizer.smart_batch_insert(tools_data, auto_chunk_size=True)