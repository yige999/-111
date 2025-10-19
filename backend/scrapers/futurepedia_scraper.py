import feedparser
import httpx
import re
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse, urljoin
import logging

from ..models import RawTool

logger = logging.getLogger(__name__)


class FuturepediaScraper:
    """Futurepedia RSS 专用抓取器"""

    def __init__(self):
        self.user_agent = "AutoSaaS-Radar-Bot/1.0"
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/rss+xml, application/xml, text/xml"
        }
        self.base_url = "https://www.futurepedia.io"

    async def fetch_futurepedia_tools(self, limit: int = 50) -> List[RawTool]:
        """抓取Futurepedia RSS中的AI工具"""
        feed_url = "https://www.futurepedia.io/feed"

        try:
            async with httpx.AsyncClient(timeout=30, headers=self.headers) as client:
                response = await client.get(feed_url)
                response.raise_for_status()

                # 解析RSS
                feed = feedparser.parse(response.content)

                if feed.bozo:
                    logger.warning(f"Futurepedia RSS解析警告: {feed.bozo_exception}")

                tools = []
                for entry in feed.entries[:limit]:
                    tool = self._parse_futurepedia_entry(entry)
                    if tool:
                        tools.append(tool)

                logger.info(f"从Futurepedia抓取到 {len(tools)} 个AI工具")
                return tools

        except httpx.HTTPError as e:
            logger.error(f"Futurepedia HTTP错误: {e}")
        except Exception as e:
            logger.error(f"Futurepedia抓取失败: {e}")

        return []

    def _parse_futurepedia_entry(self, entry) -> Optional[RawTool]:
        """解析Futurepedia RSS条目"""
        try:
            title = getattr(entry, 'title', '').strip()
            description = getattr(entry, 'description', getattr(entry, 'summary', '')).strip()
            link = getattr(entry, 'link', '').strip()

            # 清理HTML标签
            description = self._clean_html(description)

            if not title or not link:
                return None

            # Futurepedia特定处理
            title = self._clean_title(title)
            votes = self._extract_votes_from_fp(entry)
            category = self._extract_category_from_fp(entry)

            # 提取日期
            date = self._extract_date(entry)

            # 标准化URL
            link = self._normalize_futurepedia_url(link)

            return RawTool(
                tool_name=title,
                description=description[:500],
                votes=votes,
                link=link,
                date=date,
                category=category
            )

        except Exception as e:
            logger.error(f"解析Futurepedia条目失败: {e}")
            return None

    def _clean_title(self, title: str) -> str:
        """清理标题，移除Futurepedia前缀"""
        # 移除常见的Futurepedia前缀
        prefixes_to_remove = [
            r'^Futurepedia\s*-\s*',
            r'^FP\s*-\s*',
            r'^\[Futurepedia\]\s*',
            r'^AI Tool\s*:\s*',
        ]

        for prefix in prefixes_to_remove:
            title = re.sub(prefix, '', title, flags=re.IGNORECASE)

        return title.strip()

    def _extract_votes_from_fp(self, entry) -> int:
        """从Futurepedia条目中提取投票数或评分"""
        description = getattr(entry, 'description', getattr(entry, 'summary', ''))

        # 查找评分或投票数
        patterns = [
            r'(\d+)\s*votes?',
            r'(\d+)\s*upvotes?',
            r'(\d+)\s*reviews?',
            r'★\s*(\d+(?:\.\d+)?)',  # 星级评分
            r'(\d+(?:\.\d+)?)\s*/\s*5',  # 5分制评分
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    # 如果是评分，转换为整数（例如4.5星 = 45票）
                    if '/' in pattern or '★' in pattern:
                        return int(score * 10)
                    return int(score)
                except ValueError:
                    continue

        return 0

    def _extract_category_from_fp(self, entry) -> str:
        """从Futurepedia条目中提取分类"""
        description = getattr(entry, 'description', getattr(entry, 'summary', ''))
        title = getattr(entry, 'title', '')

        text_to_check = (title + ' ' + description).lower()

        # AI工具分类映射
        category_keywords = {
            'Video': ['video', 'video generation', 'video editing', 'animation', 'video creation'],
            'Text': ['text', 'writing', 'content creation', 'copywriting', 'text generation'],
            'Productivity': ['productivity', 'automation', 'workflow', 'efficiency', 'task management'],
            'Marketing': ['marketing', 'seo', 'social media', 'advertising', 'email marketing'],
            'Education': ['education', 'learning', 'tutoring', 'course creation', 'teaching'],
            'Audio': ['audio', 'music', 'voice', 'sound', 'podcast', 'speech'],
            'Image': ['image', 'image generation', 'photo editing', 'graphics', 'design'],
            'Code': ['code', 'programming', 'development', 'coding', 'software development']
        }

        for category, keywords in category_keywords.items():
            if any(keyword in text_to_check for keyword in keywords):
                return category

        return ""

    def _normalize_futurepedia_url(self, url: str) -> str:
        """标准化Futurepedia URL"""
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


async def fetch_futurepedia_tools(limit: int = 50) -> List[RawTool]:
    """便捷函数：抓取Futurepedia AI工具"""
    scraper = FuturepediaScraper()
    return await scraper.fetch_futurepedia_tools(limit)