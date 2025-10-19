import feedparser
import httpx
from datetime import datetime, timezone
from typing import List, Optional
import re
from urllib.parse import urljoin, urlparse
import logging

from ..models import RawTool

logger = logging.getLogger(__name__)


class RSScraper:
    """RSS feed 抓取器"""

    def __init__(self, user_agent: str = "AutoSaaS-Radar-Bot/1.0"):
        self.user_agent = user_agent
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "application/rss+xml, application/xml, text/xml"
        }

    async def fetch_feed(self, feed_url: str, timeout: int = 30) -> Optional[List[RawTool]]:
        """抓取单个RSS feed"""
        try:
            async with httpx.AsyncClient(timeout=timeout, headers=self.headers) as client:
                response = await client.get(feed_url)
                response.raise_for_status()

                # 解析RSS
                feed = feedparser.parse(response.content)

                if feed.bozo:
                    logger.warning(f"RSS解析警告 {feed_url}: {feed.bozo_exception}")

                tools = []
                for entry in feed.entries:
                    tool = self._parse_entry(entry, feed_url)
                    if tool:
                        tools.append(tool)

                logger.info(f"从 {feed_url} 抓取到 {len(tools)} 个工具")
                return tools

        except httpx.HTTPError as e:
            logger.error(f"HTTP错误抓取 {feed_url}: {e}")
        except Exception as e:
            logger.error(f"抓取RSS {feed_url} 失败: {e}")

        return None

    def _parse_entry(self, entry, feed_url: str) -> Optional[RawTool]:
        """解析RSS条目"""
        try:
            # 提取基本信息
            title = getattr(entry, 'title', '').strip()
            description = getattr(entry, 'description', getattr(entry, 'summary', '')).strip()
            link = getattr(entry, 'link', '').strip()

            # 清理HTML标签
            description = self._clean_html(description)

            # 验证必要字段
            if not title or not link:
                return None

            # 提取日期
            date = self._extract_date(entry)

            # 提取投票数（如果有的话）
            votes = self._extract_votes(entry)

            # 标准化URL
            link = self._normalize_url(link, feed_url)

            return RawTool(
                tool_name=title,
                description=description[:500],  # 限制描述长度
                votes=votes,
                link=link,
                date=date,
                category=""
            )

        except Exception as e:
            logger.error(f"解析RSS条目失败: {e}")
            return None

    def _clean_html(self, text: str) -> str:
        """清理HTML标签"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()

    def _extract_date(self, entry) -> datetime:
        """提取发布日期"""
        # 尝试多种日期字段
        date_fields = ['published_parsed', 'updated_parsed']

        for field in date_fields:
            if hasattr(entry, field):
                time_struct = getattr(entry, field)
                if time_struct:
                    try:
                        return datetime(*time_struct[:6], tzinfo=timezone.utc)
                    except (ValueError, TypeError):
                        continue

        # 默认使用当前时间
        return datetime.now(timezone.utc)

    def _extract_votes(self, entry) -> int:
        """提取投票数"""
        # 从描述中提取可能的投票数
        description = getattr(entry, 'description', getattr(entry, 'summary', ''))

        # 匹配常见的投票数格式
        vote_patterns = [
            r'(\d+)\s*votes?',
            r'(\d+)\s*upvotes?',
            r'(\d+)\s*👍',
            r'(\d+)\s*♥',
        ]

        for pattern in vote_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        return 0

    def _normalize_url(self, url: str, base_url: str) -> str:
        """标准化URL"""
        if not url:
            return ""

        # 移除UTM参数
        url = re.sub(r'[?&]utm_[^&]*', '', url)
        url = re.sub(r'[?&]ref=[^&]*', '', url)

        # 确保是完整URL
        if not url.startswith(('http://', 'https://')):
            base_domain = urlparse(base_url).netloc
            url = urljoin(f"https://{base_domain}", url)

        return url


async def fetch_all_feeds(feed_urls: List[str]) -> List[RawTool]:
    """抓取所有RSS feeds"""
    scraper = RSScraper()
    all_tools = []

    for feed_url in feed_urls:
        logger.info(f"开始抓取RSS: {feed_url}")
        tools = await scraper.fetch_feed(feed_url)
        if tools:
            all_tools.extend(tools)

    # 去重（基于链接）
    seen_links = set()
    unique_tools = []
    for tool in all_tools:
        if tool.link not in seen_links:
            seen_links.add(tool.link)
            unique_tools.append(tool)

    logger.info(f"总共抓取到 {len(unique_tools)} 个唯一工具")
    return unique_tools