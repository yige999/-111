"""
批量插入优化器 - 提供高性能批量数据处理
"""
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
import time

from .database_manager import DatabaseManager, db_manager

logger = logging.getLogger(__name__)

class BatchOptimizer:
    """批量插入优化器"""

    def __init__(self, db_manager: DatabaseManager = None, batch_size: int = 50, max_workers: int = 4):
        self.db_manager = db_manager or db_manager
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process_large_batch(self, tools_data: List[Dict[str, Any]],
                                progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """处理大批量数据"""
        start_time = time.time()
        total_items = len(tools_data)

        if total_items == 0:
            return {"total": 0, "success": 0, "failed": 0, "duplicates": 0, "time": 0}

        logger.info(f"开始处理大批量数据: {total_items} 项")

        # 分块处理
        chunks = self._create_chunks(tools_data, self.batch_size)
        total_chunks = len(chunks)

        stats = {"success": 0, "failed": 0, "duplicates": 0}

        # 并发处理块
        semaphore = asyncio.Semaphore(self.max_workers)
        tasks = []

        for i, chunk in enumerate(chunks):
            task = self._process_chunk_with_semaphore(semaphore, chunk, i + 1, total_chunks)
            tasks.append(task)

        # 等待所有任务完成
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 汇总结果
        for i, result in enumerate(chunk_results):
            if isinstance(result, Exception):
                logger.error(f"块 {i + 1} 处理失败: {result}")
                # 假设整个块失败
                chunk_size = len(chunks[i]) if i < len(chunks) else 0
                stats["failed"] += chunk_size
            else:
                stats["success"] += result.get("success", 0)
                stats["failed"] += result.get("failed", 0)
                stats["duplicates"] += result.get("duplicates", 0)

            # 调用进度回调
            if progress_callback:
                progress = (i + 1) / total_chunks * 100
                try:
                    await progress_callback(progress, stats, i + 1, total_chunks)
                except Exception as e:
                    logger.warning(f"进度回调失败: {e}")

        end_time = time.time()
        processing_time = end_time - start_time

        # 添加总计数
        stats["total"] = total_items
        stats["time"] = round(processing_time, 2)
        stats["items_per_second"] = round(total_items / processing_time, 2) if processing_time > 0 else 0

        logger.info(f"批量处理完成: {stats}")

        return stats

    async def _process_chunk_with_semaphore(self, semaphore: asyncio.Semaphore,
                                          chunk: List[Dict[str, Any]],
                                          chunk_num: int, total_chunks: int) -> Dict[str, int]:
        """使用信号量处理块"""
        async with semaphore:
            return await self._process_chunk(chunk, chunk_num, total_chunks)

    async def _process_chunk(self, chunk: List[Dict[str, Any]],
                           chunk_num: int, total_chunks: int) -> Dict[str, int]:
        """处理单个数据块"""
        try:
            logger.debug(f"处理块 {chunk_num}/{total_chunks}: {len(chunk)} 项")

            # 使用数据库管理器的批量插入
            result = await self.db_manager.batch_insert_tools(chunk)

            logger.debug(f"块 {chunk_num} 完成: {result}")
            return result

        except Exception as e:
            logger.error(f"处理块 {chunk_num} 失败: {e}")
            return {"success": 0, "failed": len(chunk), "duplicates": 0}

    def _create_chunks(self, data: List[Dict[str, Any]], chunk_size: int) -> List[List[Dict[str, Any]]]:
        """创建数据块"""
        chunks = []
        for i in range(0, len(data), chunk_size):
            chunks.append(data[i:i + chunk_size])
        return chunks

    async def smart_batch_insert(self, tools_data: List[Dict[str, Any]],
                               auto_chunk_size: bool = True) -> Dict[str, Any]:
        """智能批量插入 - 自动调整批次大小"""
        total_items = len(tools_data)

        if total_items == 0:
            return {"total": 0, "success": 0, "failed": 0, "duplicates": 0, "time": 0}

        # 自动调整批次大小
        if auto_chunk_size:
            optimal_batch_size = self._calculate_optimal_batch_size(total_items)
            self.batch_size = optimal_batch_size
            logger.info(f"自动调整批次大小为: {optimal_batch_size}")

        # 预处理数据 - 去重和验证
        processed_data = await self._preprocess_data(tools_data)

        # 执行批量插入
        return await self.process_large_batch(processed_data)

    async def _preprocess_data(self, tools_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """预处理数据 - 去重和基本验证"""
        seen = set()
        processed_data = []

        for tool in tools_data:
            # 创建唯一键
            tool_name = tool.get('tool_name', '').strip().lower()
            link = tool.get('link', '').strip()
            unique_key = f"{tool_name}|{link}"

            # 跳过重复项
            if unique_key in seen:
                continue

            # 基本验证
            if not tool_name:
                continue

            seen.add(unique_key)
            processed_data.append(tool)

        logger.info(f"预处理完成: 原始 {len(tools_data)} 项，处理后 {len(processed_data)} 项")
        return processed_data

    def _calculate_optimal_batch_size(self, total_items: int) -> int:
        """计算最优批次大小"""
        if total_items < 20:
            return total_items
        elif total_items < 100:
            return 20
        elif total_items < 500:
            return 50
        elif total_items < 2000:
            return 100
        else:
            return 200

    async def incremental_insert(self, tools_data: List[Dict[str, Any]],
                               checkpoint_interval: int = 100) -> Dict[str, Any]:
        """增量插入 - 支持断点续传"""
        total_items = len(tools_data)

        if total_items == 0:
            return {"total": 0, "success": 0, "failed": 0, "duplicates": 0, "time": 0}

        logger.info(f"开始增量插入: {total_items} 项，检查点间隔: {checkpoint_interval}")

        stats = {"success": 0, "failed": 0, "duplicates": 0}
        start_time = time.time()

        # 分检查点处理
        for i in range(0, total_items, checkpoint_interval):
            end_idx = min(i + checkpoint_interval, total_items)
            chunk = tools_data[i:end_idx]

            try:
                # 处理当前检查点
                chunk_result = await self.db_manager.batch_insert_tools(chunk)

                # 更新统计
                stats["success"] += chunk_result.get("success", 0)
                stats["failed"] += chunk_result.get("failed", 0)
                stats["duplicates"] += chunk_result.get("duplicates", 0)

                logger.info(f"检查点 {i//checkpoint_interval + 1} 完成: {chunk_result}")

            except Exception as e:
                logger.error(f"检查点 {i//checkpoint_interval + 1} 失败: {e}")
                stats["failed"] += len(chunk)

        end_time = time.time()

        # 添加统计信息
        stats["total"] = total_items
        stats["time"] = round(end_time - start_time, 2)
        stats["items_per_second"] = round(total_items / (end_time - start_time), 2)

        logger.info(f"增量插入完成: {stats}")
        return stats

    async def benchmark_performance(self, test_data: List[Dict[str, Any]],
                                  batch_sizes: List[int] = None) -> Dict[str, Any]:
        """性能基准测试"""
        if batch_sizes is None:
            batch_sizes = [10, 25, 50, 100, 200]

        logger.info(f"开始性能基准测试: {len(test_data)} 项，批次大小: {batch_sizes}")

        benchmark_results = {}

        for batch_size in batch_sizes:
            logger.info(f"测试批次大小: {batch_size}")

            self.batch_size = batch_size
            start_time = time.time()

            try:
                result = await self.process_large_batch(test_data)
                end_time = time.time()

                benchmark_results[batch_size] = {
                    "total_time": round(end_time - start_time, 2),
                    "items_per_second": round(len(test_data) / (end_time - start_time), 2),
                    "success_rate": round(result.get("success", 0) / len(test_data) * 100, 2),
                    "result": result
                }

                logger.info(f"批次大小 {batch_size} 结果: {benchmark_results[batch_size]['items_per_second']} 项/秒")

            except Exception as e:
                logger.error(f"批次大小 {batch_size} 测试失败: {e}")
                benchmark_results[batch_size] = {"error": str(e)}

        # 找出最佳批次大小
        best_batch_size = None
        best_performance = 0

        for batch_size, result in benchmark_results.items():
            if "items_per_second" in result and result["items_per_second"] > best_performance:
                best_performance = result["items_per_second"]
                best_batch_size = batch_size

        logger.info(f"最佳批次大小: {best_batch_size} ({best_performance} 项/秒)")

        return {
            "best_batch_size": best_batch_size,
            "best_performance": best_performance,
            "detailed_results": benchmark_results
        }

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

# 创建全局批量优化器实例
batch_optimizer = BatchOptimizer()