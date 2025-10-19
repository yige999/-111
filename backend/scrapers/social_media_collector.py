import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime

from .reddit_scraper import RedditScraper
from .hackernews_scraper import HackerNewsScraper
from app.models.tool import RawToolData
from app.core.config import settings

logger = logging.getLogger(__name__)


class SocialMediaCollector:
    """社媒抓取器统一接口 - 整合Reddit和Hacker News抓取功能"""

    def __init__(self):
        self.reddit_scraper = RedditScraper()
        self.hackernews_scraper = HackerNewsScraper()
        self.enabled_sources = {
            "reddit": True,
            "hackernews": True
        }

    async def initialize(self):
        """初始化所有抓取器"""
        try:
            if self.enabled_sources["reddit"]:
                await self.reddit_scraper.initialize()
                logger.info("Reddit抓取器初始化成功")

            if self.enabled_sources["hackernews"]:
                await self.hackernews_scraper.initialize()
                logger.info("Hacker News抓取器初始化成功")

            logger.info("所有社媒抓取器初始化完成")

        except Exception as e:
            logger.error(f"社媒抓取器初始化失败: {e}")
            raise

    async def close(self):
        """关闭所有抓取器"""
        try:
            if self.enabled_sources["reddit"]:
                await self.reddit_scraper.close()

            if self.enabled_sources["hackernews"]:
                await self.hackernews_scraper.close()

            logger.info("所有社媒抓取器已关闭")

        except Exception as e:
            logger.error(f"关闭社媒抓取器失败: {e}")

    async def scrape_all_sources(self, limit_per_source: int = 25) -> List[RawToolData]:
        """从所有启用的数据源抓取数据"""
        logger.info(f"开始从所有社媒数据源抓取数据，每源限制: {limit_per_source}")

        all_tools = []
        tasks = []

        # 添加Reddit抓取任务
        if self.enabled_sources["reddit"]:
            tasks.append(self._scrape_reddit_with_limit(limit_per_source))

        # 添加Hacker News抓取任务
        if self.enabled_sources["hackernews"]:
            tasks.append(self._scrape_hackernews_with_limit(limit_per_source))

        # 并发执行所有抓取任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                source_name = "Reddit" if i == 0 and self.enabled_sources["reddit"] else "Hacker News"
                logger.error(f"{source_name}抓取失败: {result}")
            elif isinstance(result, list):
                all_tools.extend(result)

        # 去重和统计
        unique_tools = self._deduplicate_tools(all_tools)
        source_stats = self._get_source_stats(unique_tools)

        logger.info(f"社媒抓取完成: 总共 {len(all_tools)} 个，去重后 {len(unique_tools)} 个")
        logger.info(f"数据源统计: {source_stats}")

        return unique_tools

    async def _scrape_reddit_with_limit(self, limit: int) -> List[RawToolData]:
        """抓取Reddit数据"""
        try:
            return await self.reddit_scraper.scrape_all_subreddits(limit)
        except Exception as e:
            logger.error(f"Reddit抓取失败: {e}")
            return []

    async def _scrape_hackernews_with_limit(self, limit: int) -> List[RawToolData]:
        """抓取Hacker News数据"""
        try:
            return await self.hackernews_scraper.scrape_hacker_news(limit)
        except Exception as e:
            logger.error(f"Hacker News抓取失败: {e}")
            return []

    def _deduplicate_tools(self, tools: List[RawToolData]) -> List[RawToolData]:
        """去重工具列表"""
        seen = set()
        unique_tools = []

        for tool in tools:
            # 使用工具名称和链接的组合作为去重键
            key = (tool.tool_name.lower().strip(), tool.link or "")
            if key not in seen:
                seen.add(key)
                unique_tools.append(tool)

        return unique_tools

    def _get_source_stats(self, tools: List[RawToolData]) -> Dict[str, int]:
        """获取数据源统计"""
        stats = {}
        for tool in tools:
            source = tool.source
            stats[source] = stats.get(source, 0) + 1
        return stats

    async def scrape_specific_source(self, source: str, limit: int = 25) -> List[RawToolData]:
        """抓取特定数据源"""
        logger.info(f"开始抓取特定数据源: {source}")

        if source.lower() == "reddit" and self.enabled_sources["reddit"]:
            return await self.reddit_scraper.scrape_all_subreddits(limit)

        elif source.lower() in ["hackernews", "hacker_news"] and self.enabled_sources["hackernews"]:
            return await self.hackernews_scraper.scrape_hacker_news(limit)

        else:
            logger.warning(f"未知或未启用的数据源: {source}")
            return []

    def enable_source(self, source: str):
        """启用数据源"""
        if source.lower() == "reddit":
            self.enabled_sources["reddit"] = True
            logger.info("Reddit数据源已启用")
        elif source.lower() in ["hackernews", "hacker_news"]:
            self.enabled_sources["hackernews"] = True
            logger.info("Hacker News数据源已启用")
        else:
            logger.warning(f"未知数据源: {source}")

    def disable_source(self, source: str):
        """禁用数据源"""
        if source.lower() == "reddit":
            self.enabled_sources["reddit"] = False
            logger.info("Reddit数据源已禁用")
        elif source.lower() in ["hackernews", "hacker_news"]:
            self.enabled_sources["hackernews"] = False
            logger.info("Hacker News数据源已禁用")
        else:
            logger.warning(f"未知数据源: {source}")

    def get_enabled_sources(self) -> List[str]:
        """获取启用的数据源列表"""
        enabled = []
        if self.enabled_sources["reddit"]:
            enabled.append("reddit")
        if self.enabled_sources["hackernews"]:
            enabled.append("hackernews")
        return enabled

    async def test_connections(self) -> Dict[str, bool]:
        """测试所有数据源连接"""
        logger.info("开始测试社媒数据源连接...")
        results = {}

        if self.enabled_sources["reddit"]:
            try:
                # 测试Reddit连接（尝试获取首页）
                test_tools = await self.reddit_scraper.scrape_all_subreddits(5)
                results["reddit"] = len(test_tools) >= 0  # 只要没有异常就算成功
                logger.info("Reddit连接测试成功")
            except Exception as e:
                results["reddit"] = False
                logger.error(f"Reddit连接测试失败: {e}")

        if self.enabled_sources["hackernews"]:
            try:
                # 测试Hacker News连接
                test_tools = await self.hackernews_scraper.scrape_hacker_news(5)
                results["hackernews"] = len(test_tools) >= 0
                logger.info("Hacker News连接测试成功")
            except Exception as e:
                results["hackernews"] = False
                logger.error(f"Hacker News连接测试失败: {e}")

        logger.info(f"连接测试结果: {results}")
        return results


# 便捷函数
async def scrape_social_media_tools(limit_per_source: int = 25) -> List[RawToolData]:
    """便捷函数：抓取所有社媒工具"""
    collector = SocialMediaCollector()
    await collector.initialize()
    try:
        return await collector.scrape_all_sources(limit_per_source)
    finally:
        await collector.close()


async def test_social_media_connections() -> Dict[str, bool]:
    """便捷函数：测试社媒连接"""
    collector = SocialMediaCollector()
    await collector.initialize()
    try:
        return await collector.test_connections()
    finally:
        await collector.close()