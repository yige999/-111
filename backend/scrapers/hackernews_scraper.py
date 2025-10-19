import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import httpx
from bs4 import BeautifulSoup

from app.models.tool import RawToolData
from app.core.config import settings

logger = logging.getLogger(__name__)


class HackerNewsScraper:
    """Hacker News 抓取器 - 从Hacker News抓取AI/SaaS相关内容"""

    def __init__(self):
        self.session = None
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.web_url = "https://news.ycombinator.com"
        self.keywords = [
            "ai", "artificial intelligence", "machine learning", "ml",
            "saas", "tool", "app", "platform", "service", "software",
            "startup", "launch", "product", "api", "sdk",
            "automation", "productivity", "b2b", "workflow",
            "openai", "gpt", "claude", "gemini", "llm",
            "chatbot", "assistant", "copilot", "automation"
        ]

    async def initialize(self):
        """初始化HTTP客户端"""
        try:
            self.session = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": settings.REDDIT_USER_AGENT
                }
            )
            logger.info("Hacker News抓取器初始化成功")
        except Exception as e:
            logger.error(f"Hacker News抓取器初始化失败: {e}")
            raise

    async def close(self):
        """关闭连接"""
        if self.session:
            await self.session.aclose()

    async def scrape_hacker_news(self, limit: int = 30) -> List[RawToolData]:
        """抓取Hacker News热门故事"""
        logger.info(f"开始抓取Hacker News内容，限制数量: {limit}")

        try:
            # 获取最新故事ID列表
            story_ids = await self._get_new_stories()
            if not story_ids:
                logger.warning("未能获取到Hacker News故事列表")
                return []

            # 限制处理数量
            story_ids = story_ids[:limit]

            # 并发获取故事详情
            tasks = [self._get_story_details(story_id) for story_id in story_ids]
            stories = await asyncio.gather(*tasks, return_exceptions=True)

            # 过滤和解析相关故事
            tools = []
            for story in stories:
                if isinstance(story, Exception):
                    logger.warning(f"获取故事详情失败: {story}")
                    continue

                if story and self._is_relevant_story(story):
                    tool = self._parse_story(story)
                    if tool:
                        tools.append(tool)

            logger.info(f"Hacker News抓取完成: 处理 {len(story_ids)} 个故事，相关工具 {len(tools)} 个")
            return tools

        except Exception as e:
            logger.error(f"Hacker News抓取失败: {e}")
            return []

    async def _get_new_stories(self) -> List[int]:
        """获取最新故事ID列表"""
        try:
            response = await self.session.get(f"{self.base_url}/newstories.json")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取Hacker News故事列表失败: {e}")
            return []

    async def _get_story_details(self, story_id: int) -> Optional[Dict]:
        """获取故事详情"""
        try:
            response = await self.session.get(f"{self.base_url}/item/{story_id}.json")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"获取故事 {story_id} 详情失败: {e}")
            return None

    def _is_relevant_story(self, story: Dict) -> bool:
        """判断故事是否相关"""
        title = story.get("title", "").lower()
        text = story.get("text", "").lower()
        url = story.get("url", "").lower()

        # 合并文本进行关键词匹配
        combined_text = f"{title} {text} {url}"

        # 计算关键词匹配数
        keyword_matches = sum(1 for keyword in self.keywords if keyword in combined_text)

        # 至少匹配1个关键词，或者标题包含明显的工具/产品词汇
        tool_indicators = ["launch", "release", "beta", "alpha", "v1", "v2", "v3", "tool", "app", "service"]
        has_tool_indicator = any(indicator in title for indicator in tool_indicators)

        return keyword_matches >= 1 or has_tool_indicator

    def _parse_story(self, story: Dict) -> Optional[RawToolData]:
        """解析故事数据"""
        try:
            title = story.get("title", "")
            score = story.get("score", 0)
            url = story.get("url")
            text = story.get("text", "")
            time = story.get("time", 0)
            story_id = story.get("id")

            # 构造最终URL
            if not url:
                url = f"{self.web_url}/item?id={story_id}"

            # 构造描述
            description = text or title
            if len(description) > 500:
                description = description[:500] + "..."

            # 提取工具名称
            tool_name = self._extract_tool_name(title)

            return RawToolData(
                tool_name=tool_name,
                description=description,
                votes=score,
                link=url,
                source="hackernews",
                date=datetime.fromtimestamp(time)
            )

        except Exception as e:
            logger.warning(f"解析Hacker News故事失败: {e}")
            return None

    def _extract_tool_name(self, title: str) -> str:
        """从标题中提取工具名称"""
        # 移除常见的Hacker News前缀
        prefixes_to_remove = [
            "Ask HN:", "Show HN:", "Launch HN:", "Tell HN:",
            "launching", "just launched", "we built", "I built",
            "introducing", "presenting", "announcing", "release",
            "beta", "alpha", "version", "v1.", "v2.", "v3."
        ]

        cleaned_title = title.lower()
        for prefix in prefixes_to_remove:
            if cleaned_title.startswith(prefix):
                cleaned_title = cleaned_title[len(prefix):].strip()

        # 提取前几个词作为工具名
        words = cleaned_title.split()
        tool_name = " ".join(words[:5])

        # 清理和格式化
        import re
        tool_name = re.sub(r'[^\w\s-]', '', tool_name).strip()
        tool_name = tool_name.title() if tool_name else title

        return tool_name


# 便捷函数
async def scrape_hackernews_tools(limit: int = 30) -> List[RawToolData]:
    """便捷函数：抓取Hacker News工具"""
    scraper = HackerNewsScraper()
    await scraper.initialize()
    try:
        return await scraper.scrape_hacker_news(limit)
    finally:
        await scraper.close()
