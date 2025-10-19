import feedparser
import httpx
import re
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse, urljoin
import logging

from ..models import RawTool

logger = logging.getLogger(__name__)


class ProductHuntScraper:
    """ProductHunt RSS 专用抓取器"""

    def __init__(self):
        self.user_agent = "AutoSaaS-Radar-Bot/1.0"
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/rss+xml, application/xml, text/xml"
        }
        self.base_url = "https://www.producthunt.com"

    async def fetch_producthunt_tools(self, limit: int = 50) -> List[RawTool]:
        """抓取ProductHunt RSS中的AI工具"""
        feed_url = "https://www.producthunt.com/feed"

        try:
            async with httpx.AsyncClient(timeout=30, headers=self.headers) as client:
                response = await client.get(feed_url)
                response.raise_for_status()

                # 解析RSS
                feed = feedparser.parse(response.content)

                if feed.bozo:
                    logger.warning(f"ProductHunt RSS解析警告: {feed.bozo_exception}")

                tools = []
                for entry in feed.entries[:limit]:
                    tool = self._parse_producthunt_entry(entry)
                    if tool and self._is_ai_related(tool):
                        tools.append(tool)

                logger.info(f"从ProductHunt筛选出 {len(tools)} 个AI工具")
                return tools

        except httpx.HTTPError as e:
            logger.error(f"ProductHunt HTTP错误: {e}")
        except Exception as e:
            logger.error(f"ProductHunt抓取失败: {e}")

        return []

    def _parse_producthunt_entry(self, entry) -> Optional[RawTool]:
        """解析ProductHunt RSS条目"""
        try:
            title = getattr(entry, 'title', '').strip()
            description = getattr(entry, 'description', getattr(entry, 'summary', '')).strip()
            link = getattr(entry, 'link', '').strip()

            # 清理HTML标签
            description = self._clean_html(description)

            if not title or not link:
                return None

            # ProductHunt特定处理
            title = self._clean_title(title)
            votes = self._extract_votes_from_ph(entry)

            # 提取日期
            date = self._extract_date(entry)

            # 标准化URL
            link = self._normalize_producthunt_url(link)

            return RawTool(
                tool_name=title,
                description=description[:500],
                votes=votes,
                link=link,
                date=date,
                category=""
            )

        except Exception as e:
            logger.error(f"解析ProductHunt条目失败: {e}")
            return None

    def _is_ai_related(self, tool: RawTool) -> bool:
        """判断是否为AI相关工具"""
        ai_keywords = [
            'AI', 'artificial intelligence', 'GPT', 'ChatGPT', 'OpenAI',
            'machine learning', 'ML', 'deep learning', 'neural network',
            'automation', 'bot', 'assistant', 'claude', 'gemini',
            '生成式', '人工智能', '智能', '自动', '助手'
        ]

        text_to_check = (tool.tool_name + ' ' + tool.description).lower()

        return any(keyword.lower() in text_to_check for keyword in ai_keywords)

    def _clean_title(self, title: str) -> str:
        """清理标题，移除ProductHunt前缀"""
        # 移除常见的ProductHunt前缀
        prefixes_to_remove = [
            r'^Product Hunt\s*-\s*',
            r'^PH\s*-\s*',
            r'^\[Product Hunt\]\s*',
        ]

        for prefix in prefixes_to_remove:
            title = re.sub(prefix, '', title, flags=re.IGNORECASE)

        return title.strip()

    def _extract_votes_from_ph(self, entry) -> int:
        """从ProductHunt条目中提取投票数"""
        # ProductHunt RSS可能在tags或summary中包含投票数
        description = getattr(entry, 'description', getattr(entry, 'summary', ''))

        # 查找投票数模式
        vote_patterns = [
            r'(\d+)\s*votes?',
            r'(\d+)\s*upvotes?',
            r'👍\s*(\d+)',
            r'↑\s*(\d+)',
        ]

        for pattern in vote_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        return 0

    def _normalize_producthunt_url(self, url: str) -> str:
        """标准化ProductHunt URL"""
        if not url:
            return ""

        # 移除UTM参数和推荐参数
        url = re.sub(r'[?&]utm_[^&]*', '', url)
        url = re.sub(r'[?&]ref=[^&]*', '', url)

        # 确保是完整URL
        if not url.startswith(('http://', 'https://')):
            url = urljoin(self.base_url, url)

        return url

    def _clean_html(self, text: str) -> str:
        """清理HTML标签"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()

    def _extract_date(self, entry) -> datetime:
        """提取发布日期"""
        date_fields = ['published_parsed', 'updated_parsed']

        for field in date_fields:
            if hasattr(entry, field):
                time_struct = getattr(entry, field)
                if time_struct:
                    try:
                        return datetime(*time_struct[:6], tzinfo=timezone.utc)
                    except (ValueError, TypeError):
                        continue

        return datetime.now(timezone.utc)


async def fetch_producthunt_tools(limit: int = 50) -> List[RawTool]:
    """便捷函数：抓取ProductHunt AI工具"""
    scraper = ProductHuntScraper()
    return await scraper.fetch_producthunt_tools(limit)