import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import feedparser
import httpx
from bs4 import BeautifulSoup

from ..core.config import settings
from ..models.tool import RawToolData

logger = logging.getLogger(__name__)


class DataCollector:
    """数据收集器 - 从各种数据源收集AI工具信息"""

    def __init__(self):
        self.session = None
        self.sources = {
            "producthunt": {
                "url": "https://www.producthunt.com/feed",
                "type": "rss",
                "enabled": True
            },
            "futurepedia": {
                "url": "https://www.futurepedia.io/feed",
                "type": "rss",
                "enabled": True
            },
            "hackernews": {
                "url": "https://hacker-news.firebaseio.com/v0/newstories.json",
                "type": "api",
                "enabled": True
            }
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": settings.REDDIT_USER_AGENT
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.aclose()

    async def collect_all_sources(self) -> List[RawToolData]:
        """从所有启用的数据源收集数据"""
        logger.info("开始从所有数据源收集数据...")

        tasks = []
        for source_name, source_config in self.sources.items():
            if source_config["enabled"]:
                if source_config["type"] == "rss":
                    tasks.append(self._collect_from_rss(source_name, source_config["url"]))
                elif source_config["type"] == "api":
                    tasks.append(self._collect_from_api(source_name, source_config["url"]))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_tools = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"数据源收集失败: {result}")
            elif isinstance(result, list):
                all_tools.extend(result)

        logger.info(f"共收集到 {len(all_tools)} 个工具数据")
        return all_tools

    async def _collect_from_rss(self, source_name: str, rss_url: str) -> List[RawToolData]:
        """从RSS源收集数据"""
        logger.info(f"正在从 {source_name} RSS源收集数据...")

        try:
            # 使用httpx获取RSS内容
            response = await self.session.get(rss_url)
            response.raise_for_status()

            # 解析RSS
            feed = feedparser.parse(response.content)

            tools = []
            for entry in feed.entries[:settings.DATA_SOURCE_LIMIT]:
                tool = self._parse_rss_entry(entry, source_name)
                if tool:
                    tools.append(tool)

            logger.info(f"从 {source_name} 收集到 {len(tools)} 个工具")
            return tools

        except Exception as e:
            logger.error(f"从 {source_name} 收集RSS数据失败: {e}")
            return []

    async def _collect_from_api(self, source_name: str, api_url: str) -> List[RawToolData]:
        """从API源收集数据"""
        logger.info(f"正在从 {source_name} API源收集数据...")

        try:
            if source_name == "hackernews":
                return await self._collect_from_hackernews()
            else:
                response = await self.session.get(api_url)
                response.raise_for_status()
                data = response.json()
                return self._parse_api_response(data, source_name)

        except Exception as e:
            logger.error(f"从 {source_name} 收集API数据失败: {e}")
            return []

    async def _collect_from_hackernews(self) -> List[RawToolData]:
        """从Hacker News收集数据"""
        try:
            # 获取最新故事ID列表
            response = await self.session.get(
                "https://hacker-news.firebaseio.com/v0/newstories.json"
            )
            response.raise_for_status()
            story_ids = response.json()[:settings.DATA_SOURCE_LIMIT]

            tools = []
            for story_id in story_ids[:10]:  # 限制处理数量
                try:
                    story_response = await self.session.get(
                        f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                    )
                    story_response.raise_for_status()
                    story_data = story_response.json()

                    # 检查是否与AI工具相关
                    if self._is_ai_tool_related(story_data):
                        tool = self._parse_hackernews_story(story_data)
                        if tool:
                            tools.append(tool)

                except Exception as e:
                    logger.warning(f"处理Hacker News故事 {story_id} 失败: {e}")
                    continue

            return tools

        except Exception as e:
            logger.error(f"从Hacker News收集数据失败: {e}")
            return []

    def _parse_rss_entry(self, entry, source_name: str) -> Optional[RawToolData]:
        """解析RSS条目"""
        try:
            # 提取工具名称
            title = entry.title if hasattr(entry, 'title') else ""

            # 提取描述
            description = ""
            if hasattr(entry, 'description'):
                description = BeautifulSoup(entry.description, 'html.parser').get_text().strip()
            elif hasattr(entry, 'summary'):
                description = BeautifulSoup(entry.summary, 'html.parser').get_text().strip()

            # 提取链接
            link = entry.link if hasattr(entry, 'link') else ""

            # 检查是否为AI工具相关
            if not self._is_ai_tool_related({"title": title, "description": description}):
                return None

            return RawToolData(
                tool_name=self._extract_tool_name(title),
                description=description,
                votes=self._extract_votes(entry),
                link=link,
                source=source_name,
                date=self._parse_date(entry)
            )

        except Exception as e:
            logger.warning(f"解析RSS条目失败: {e}")
            return None

    def _parse_hackernews_story(self, story_data: dict) -> Optional[RawToolData]:
        """解析Hacker News故事"""
        try:
            title = story_data.get("title", "")
            url = story_data.get("url", "")
            score = story_data.get("score", 0)

            if not url:
                url = f"https://news.ycombinator.com/item?id={story_data.get('id', '')}"

            description = f"Hacker News讨论: {title}"

            return RawToolData(
                tool_name=self._extract_tool_name(title),
                description=description,
                votes=score,
                link=url,
                source="hackernews",
                date=datetime.fromtimestamp(story_data.get("time", 0))
            )

        except Exception as e:
            logger.warning(f"解析Hacker News故事失败: {e}")
            return None

    def _parse_api_response(self, data: dict, source_name: str) -> List[RawToolData]:
        """解析API响应（通用方法）"""
        # 这里可以根据不同API的响应格式进行解析
        # 目前返回空列表，可以根据需要扩展
        return []

    def _is_ai_tool_related(self, item: dict) -> bool:
        """判断是否与AI工具相关"""
        title = item.get("title", "").lower()
        description = item.get("description", "").lower()

        # AI相关关键词
        ai_keywords = [
            "ai", "artificial intelligence", "machine learning", "ml",
            "gpt", "chatgpt", "openai", "claude", "gemini", "bard",
            "automation", "ai-powered", "smart", "intelligent",
            "neural", "deep learning", "nlp", "computer vision",
            "saas", "tool", "platform", "service"
        ]

        # 检查标题和描述中是否包含AI关键词
        text_content = f"{title} {description}"
        return any(keyword in text_content for keyword in ai_keywords)

    def _extract_tool_name(self, title: str) -> str:
        """从标题中提取工具名称"""
        # 移除常见的修饰词
        stop_words = [
            "new", "launch", "announcement", "introducing", "presenting",
            "beta", "alpha", "v1", "v2", "v3", "version", "update",
            "ai", "ai-powered", "smart", "intelligent"
        ]

        words = title.split()
        filtered_words = [word for word in words if word.lower() not in stop_words]

        # 取前几个词作为工具名
        tool_name = " ".join(filtered_words[:5])

        # 清理标点符号
        import re
        tool_name = re.sub(r'[^\w\s-]', '', tool_name).strip()

        return tool_name if tool_name else title

    def _extract_votes(self, entry) -> int:
        """提取投票数"""
        # 尝试从不同字段提取投票数
        if hasattr(entry, 'votes'):
            return int(entry.votes) if entry.votes else 0
        elif hasattr(entry, 'score'):
            return int(entry.score) if entry.score else 0
        elif hasattr(entry, 'comments'):
            # 如果只有评论数，用作投票数的近似
            return int(entry.comments) if entry.comments else 0
        return 0

    def _parse_date(self, entry) -> datetime:
        """解析日期"""
        # 尝试从不同字段解析日期
        date_fields = ['published', 'updated', 'created']

        for field in date_fields:
            if hasattr(entry, field):
                date_value = getattr(entry, field)
                if isinstance(date_value, str):
                    try:
                        # 尝试解析ISO格式
                        return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                    except:
                        continue
                elif hasattr(date_value, 'timetuple'):
                    # 处理结构化时间
                    import time
                    return datetime.fromtimestamp(time.mktime(date_value.timetuple()))

        # 如果无法解析，返回当前时间
        return datetime.utcnow()