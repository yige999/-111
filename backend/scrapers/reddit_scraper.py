import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import httpx
from bs4 import BeautifulSoup

from app.models.tool import RawToolData
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedditScraper:
    """Reddit 抓取器 - 从指定subreddit抓取SaaS相关内容"""

    def __init__(self):
        self.session = None
        self.subreddits = ["SaaS", "SideProject", "MicroSaaS", "IndieHackers"]
        self.keywords = [
            "saas", "tool", "app", "platform", "service", "software",
            "startup", "launch", "product", "solution", "automation",
            "ai", "automation", "productivity", "b2b", "workflow"
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
            logger.info("Reddit抓取器初始化成功（网页抓取模式）")
        except Exception as e:
            logger.error(f"Reddit抓取器初始化失败: {e}")
            raise

    async def close(self):
        """关闭连接"""
        if self.session:
            await self.session.aclose()

    async def scrape_all_subreddits(self, limit: int = 25) -> List[RawToolData]:
        """抓取所有配置的subreddit"""
        logger.info(f"开始抓取Reddit内容，限制数量: {limit}")

        all_tools = []
        tasks = []

        for subreddit_name in self.subreddits:
            tasks.append(self._scrape_subreddit_web(subreddit_name, limit))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"抓取subreddit失败: {result}")
            elif isinstance(result, list):
                all_tools.extend(result)

        # 去重和过滤
        unique_tools = self._deduplicate_tools(all_tools)
        filtered_tools = [tool for tool in unique_tools if self._is_relevant_tool(tool)]

        logger.info(f"Reddit抓取完成: 总共 {len(all_tools)} 个，去重后 {len(unique_tools)} 个，相关 {len(filtered_tools)} 个")
        return filtered_tools

    async def _scrape_subreddit_web(self, subreddit_name: str, limit: int) -> List[RawToolData]:
        """使用网页抓取模式抓取subreddit"""
        try:
            url = f"https://www.reddit.com/r/{subreddit_name}/hot/"
            tools = []

            response = await self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Reddit的帖子结构
            posts = soup.find_all('div', {'data-testid': 'post-container'})
            if not posts:
                # 备用选择器
                posts = soup.find_all('div', {'class': 'thing'})

            for i, post in enumerate(posts[:limit]):
                try:
                    tool = self._parse_web_post(post, subreddit_name)
                    if tool:
                        tools.append(tool)
                except Exception as e:
                    logger.warning(f"解析Reddit帖子失败: {e}")
                    continue

            logger.info(f"从 r/{subreddit_name} 网页抓取到 {len(tools)} 个相关工具")
            return tools

        except Exception as e:
            logger.error(f"网页抓取 r/{subreddit_name} 失败: {e}")
            return []

    def _is_relevant_tool(self, tool: RawToolData) -> bool:
        """判断工具是否相关"""
        text = f"{tool.tool_name} {tool.description or ''}".lower()
        keyword_matches = sum(1 for keyword in self.keywords if keyword in text)
        return keyword_matches >= 1

    def _parse_web_post(self, post, subreddit_name: str) -> Optional[RawToolData]:
        """解析网页抓取的Reddit帖子"""
        try:
            # 尝试多种选择器来提取标题
            title_element = None
            title_selectors = [
                'h3[data-testid="post-content-title"]',
                'h3._eYtD2XCVieq6emjKBH3m',
                'a.title',
                'p.title',
                'h2'
            ]

            for selector in title_selectors:
                title_element = post.find('h3') if selector == 'h3' else post.select_one(selector)
                if title_element:
                    break

            if not title_element:
                return None

            title = title_element.get_text().strip()

            # 提取投票数
            vote_element = post.find('div', {'data-testid': 'post-vote-score'})
            if not vote_element:
                vote_element = post.find('div', {'class': 'score'})
            votes = 0
            if vote_element:
                vote_text = vote_element.get_text().strip()
                try:
                    votes = int(''.join(filter(str.isdigit, vote_text)))
                except:
                    votes = 0

            # 提取链接
            link_element = post.find('a', {'data-testid': 'post-content-link'})
            if not link_element:
                link_element = post.find('a', {'class': 'title'})

            url = None
            if link_element:
                url = link_element.get('href')
                if url and url.startswith('/'):
                    url = f"https://reddit.com{url}"

            # 提取描述
            desc_element = post.find('div', {'data-testid': 'post-content'})
            if not desc_element:
                desc_element = post.find('div', {'class': 'usertext-body'})

            description = ""
            if desc_element:
                description = desc_element.get_text().strip()
            else:
                description = title

            if len(description) > 500:
                description = description[:500] + "..."

            # 如果没有外部链接，使用Reddit链接
            if not url:
                permalink_element = post.find('a', {'data-permalink'})
                if permalink_element:
                    url = f"https://reddit.com{permalink_element.get('data-permalink')}"
                else:
                    url = f"https://reddit.com/r/{subreddit_name}/"

            tool_name = self._extract_tool_name(title)

            return RawToolData(
                tool_name=tool_name,
                description=description,
                votes=votes,
                link=url,
                source=f"reddit_{subreddit_name}",
                date=datetime.utcnow()
            )

        except Exception as e:
            logger.warning(f"解析Reddit网页帖子失败: {e}")
            return None

    def _extract_tool_name(self, title: str) -> str:
        """从标题中提取工具名称"""
        # 移除常见的Reddit前缀
        prefixes_to_remove = [
            "[Release]", "[Launch]", "[Beta]", "[Alpha]", "[Update]",
            "[Show]", "[Ask]", "[Discuss]", "[Tool]", "[App]",
            "launching", "just launched", "we built", "I built",
            "introducing", "presenting", "announcing"
        ]

        cleaned_title = title.lower()
        for prefix in prefixes_to_remove:
            cleaned_title = cleaned_title.replace(prefix.lower(), "")

        # 提取前几个词作为工具名
        words = cleaned_title.split()
        tool_name = " ".join(words[:5])

        # 清理和格式化
        import re
        tool_name = re.sub(r'[^\w\s-]', '', tool_name).strip()
        tool_name = tool_name.title() if tool_name else title

        return tool_name

    def _deduplicate_tools(self, tools: List[RawToolData]) -> List[RawToolData]:
        """去重工具列表"""
        seen = set()
        unique_tools = []

        for tool in tools:
            # 使用工具名称作为去重键
            key = tool.tool_name.lower().strip()
            if key not in seen:
                seen.add(key)
                unique_tools.append(tool)

        return unique_tools


# 便捷函数
async def scrape_reddit_tools(limit: int = 25) -> List[RawToolData]:
    """便捷函数：抓取Reddit工具"""
    scraper = RedditScraper()
    await scraper.initialize()
    try:
        return await scraper.scrape_all_subreddits(limit)
    finally:
        await scraper.close()
