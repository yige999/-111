import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

from .producthunt_scraper import fetch_producthunt_tools
from .futurepedia_scraper import fetch_futurepedia_tools
from .data_cleaner import clean_and_validate_tools
from ..models import RawTool

logger = logging.getLogger(__name__)


class RSSManager:
    """RSS抓取管理器 - 统一管理所有RSS源"""

    def __init__(self, max_retries: int = 3, timeout: int = 30):
        self.max_retries = max_retries
        self.timeout = timeout
        self.supported_sources = {
            'producthunt': {
                'fetcher': fetch_producthunt_tools,
                'description': 'ProductHunt - 最新AI工具发现平台',
                'priority': 1
            },
            'futurepedia': {
                'fetcher': fetch_futurepedia_tools,
                'description': 'Futurepedia - AI工具目录',
                'priority': 2
            }
        }

    async def fetch_all_rss_sources(self, limit_per_source: int = 50) -> Dict[str, Any]:
        """从所有RSS源抓取数据"""
        results = {
            'success': True,
            'total_tools': 0,
            'sources': {},
            'cleaned_tools': [],
            'errors': [],
            'fetch_time': datetime.utcnow().isoformat()
        }

        logger.info("开始从所有RSS源抓取数据")

        tasks = []
        source_names = []

        # 为每个源创建抓取任务
        for source_name, source_config in self.supported_sources.items():
            task = asyncio.create_task(
                self._fetch_single_source_with_retry(source_name, source_config, limit_per_source)
            )
            tasks.append(task)
            source_names.append(source_name)

        # 并行执行所有抓取任务
        if tasks:
            source_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            for i, result in enumerate(source_results):
                source_name = source_names[i]

                if isinstance(result, Exception):
                    error_msg = f"RSS源 {source_name} 抓取失败: {str(result)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['sources'][source_name] = {
                        'success': False,
                        'error': str(result),
                        'tools_count': 0
                    }
                else:
                    results['sources'][source_name] = result
                    results['total_tools'] += result.get('tools_count', 0)

        # 清洗和去重所有工具
        all_tools = []
        for source_result in results['sources'].values():
            if source_result.get('success') and source_result.get('tools'):
                all_tools.extend(source_result['tools'])

        if all_tools:
            logger.info(f"开始清洗 {len(all_tools)} 个工具数据")
            cleaned_tools = clean_and_validate_tools(all_tools)
            results['cleaned_tools'] = cleaned_tools
            results['cleaned_count'] = len(cleaned_tools)
        else:
            results['cleaned_tools'] = []
            results['cleaned_count'] = 0

        # 确定整体成功状态
        results['success'] = len(results['errors']) == 0 and results['cleaned_count'] > 0

        logger.info(f"RSS抓取完成 - 总计: {results['total_tools']}, 清洗后: {results['cleaned_count']}")
        if results['errors']:
            logger.warning(f"发生错误: {len(results['errors'])} 个")

        return results

    async def _fetch_single_source_with_retry(self, source_name: str, source_config: Dict, limit: int) -> Dict[str, Any]:
        """带重试机制的单源抓取"""
        fetcher = source_config['fetcher']

        for attempt in range(self.max_retries):
            try:
                logger.info(f"尝试抓取 {source_name} (第 {attempt + 1}/{self.max_retries} 次)")

                tools = await fetcher(limit)

                if tools:
                    result = {
                        'success': True,
                        'tools': tools,
                        'tools_count': len(tools),
                        'description': source_config['description'],
                        'attempt': attempt + 1
                    }
                    logger.info(f"{source_name} 抓取成功: {len(tools)} 个工具")
                    return result
                else:
                    logger.warning(f"{source_name} 抓取结果为空")

            except Exception as e:
                logger.warning(f"{source_name} 第 {attempt + 1} 次尝试失败: {str(e)}")

                if attempt < self.max_retries - 1:
                    # 等待后重试
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                else:
                    # 最后一次尝试失败
                    raise e

        # 如果所有尝试都失败
        raise Exception(f"所有 {self.max_retries} 次尝试都失败")

    async def fetch_specific_sources(self, source_names: List[str], limit_per_source: int = 50) -> Dict[str, Any]:
        """从指定的RSS源抓取数据"""
        if not source_names:
            return {'success': False, 'error': '未指定任何RSS源'}

        # 验证源名称
        invalid_sources = [name for name in source_names if name not in self.supported_sources]
        if invalid_sources:
            return {
                'success': False,
                'error': f'不支持的RSS源: {invalid_sources}',
                'supported_sources': list(self.supported_sources.keys())
            }

        # 临时构建支持的源
        temp_supported = {name: self.supported_sources[name] for name in source_names}
        original_supported = self.supported_sources
        self.supported_sources = temp_supported

        try:
            result = await self.fetch_all_rss_sources(limit_per_source)
            return result
        finally:
            # 恢复原始配置
            self.supported_sources = original_supported

    def get_supported_sources(self) -> Dict[str, str]:
        """获取支持的RSS源列表"""
        return {
            name: config['description']
            for name, config in self.supported_sources.items()
        }

    def get_source_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有源的状态信息"""
        return {
            name: {
                'description': config['description'],
                'priority': config['priority'],
                'available': True
            }
            for name, config in self.supported_sources.items()
        }


# 全局RSS管理器实例
rss_manager = RSSManager()


async def fetch_ai_tools_from_rss(sources: List[str] = None, limit_per_source: int = 50) -> Dict[str, Any]:
    """便捷函数：从RSS源抓取AI工具

    Args:
        sources: RSS源列表，None表示所有源
        limit_per_source: 每个源的最大工具数量

    Returns:
        包含抓取结果的字典
    """
    if sources:
        return await rss_manager.fetch_specific_sources(sources, limit_per_source)
    else:
        return await rss_manager.fetch_all_rss_sources(limit_per_source)


def get_rss_sources_info() -> Dict[str, str]:
    """便捷函数：获取支持的RSS源信息"""
    return rss_manager.get_supported_sources()