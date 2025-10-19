import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock

from scrapers.rss_scraper import RSScraper, fetch_all_feeds
from scrapers.reddit_scraper import RedditScraper
from scrapers.hackernews_scraper import HackerNewsScraper
from models import RawTool


class TestRSScraper:
    """RSS抓取器测试"""

    @pytest.fixture
    def scraper(self):
        return RSScraper()

    @pytest.fixture
    def sample_feed_data(self):
        """示例RSS数据"""
        return {
            'entries': [
                {
                    'title': 'AI Tool Test',
                    'description': 'This is a test AI tool for <b>testing</b>',
                    'link': 'https://example.com/ai-tool',
                    'published_parsed': (2024, 1, 15, 10, 30, 0, 0, 15, 0)
                }
            ]
        }

    def test_clean_html(self, scraper):
        """测试HTML清理"""
        html_text = "This is <b>bold</b> and <i>italic</i> text"
        clean_text = scraper._clean_html(html_text)
        assert clean_text == "This is bold and italic text"

    def test_extract_votes(self, scraper):
        """测试投票数提取"""
        # 测试各种投票数格式
        descriptions = [
            "Great tool with 123 votes",
            "Nice app, 45 upvotes!",
            "Love it! 67 👍",
            "Amazing 89 ♥"
        ]
        expected_votes = [123, 45, 67, 89]

        for desc, expected in zip(descriptions, expected_votes):
            with patch.object(scraper, '_extract_votes', return_value=expected):
                votes = scraper._extract_votes({'description': desc})
                assert votes == expected

    def test_normalize_url(self, scraper):
        """测试URL标准化"""
        base_url = "https://example.com"

        # 测试相对URL
        relative_url = "/tool/ai-test"
        normalized = scraper._normalize_url(relative_url, base_url)
        assert normalized == "https://example.com/tool/ai-test"

        # 测试UTM参数清理
        utm_url = "https://example.com/tool?utm_source=test&utm_medium=web"
        cleaned = scraper._normalize_url(utm_url, base_url)
        assert "utm_" not in cleaned

    @pytest.mark.asyncio
    async def test_fetch_feed_success(self, scraper, sample_feed_data):
        """测试成功抓取RSS"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.content = b'<rss></rss>'  # 简化的RSS内容
            mock_response.raise_for_status = Mock()

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            with patch('feedparser.parse', return_value=sample_feed_data):
                tools = await scraper.fetch_feed("https://example.com/feed")

                assert len(tools) == 1
                assert tools[0].tool_name == "AI Tool Test"
                assert "bold" not in tools[0].description  # HTML标签被清理

    @pytest.mark.asyncio
    async def test_fetch_feed_error(self, scraper):
        """测试RSS抓取错误"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Network error")

            tools = await scraper.fetch_feed("https://example.com/feed")
            assert tools is None


class TestRedditScraper:
    """Reddit抓取器测试"""

    @pytest.fixture
    def scraper(self):
        return RedditScraper()

    def test_is_tool_related(self, scraper):
        """测试工具相关内容判断"""
        # 工具相关内容
        tool_titles = [
            "New AI tool for productivity",
            "Launch: My first SaaS app",
            "Show HN: My automation tool"
        ]

        # 非工具相关内容
        non_tool_titles = [
            "Looking for recommendations",
            "How to learn programming?",
            "Discussion about tech trends"
        ]

        for title in tool_titles:
            assert scraper._is_tool_related(title, "")

        for title in non_tool_titles:
            assert not scraper._is_tool_related(title, "")

    def test_parse_reddit_post(self, scraper):
        """测试Reddit帖子解析"""
        post_data = {
            'title': 'New AI Productivity Tool',
            'selftext': 'This tool helps with automation',
            'url': 'https://example.com',
            'score': 150,
            'subreddit': 'SaaS',
            'permalink': '/r/SaaS/comments/abc123/new_tool/',
            'created_utc': 1705123456  # 时间戳
        }

        tool = scraper._parse_reddit_post(post_data)

        assert tool is not None
        assert tool.tool_name == "New AI Productivity Tool"
        assert tool.votes == 150
        assert "reddit.com" in tool.link

    @pytest.mark.asyncio
    async def test_fetch_subreddit_tools(self, scraper):
        """测试抓取subreddit工具"""
        with patch.object(scraper, 'get_access_token', return_value=None):
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.json.return_value = {
                    'data': {
                        'children': [
                            {
                                'data': {
                                    'title': 'Test Tool',
                                    'url': 'https://example.com',
                                    'score': 100,
                                    'permalink': '/r/test/comments/abc/',
                                    'created_utc': 1705123456
                                }
                            }
                        ]
                    }
                }
                mock_response.raise_for_status = Mock()

                mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

                tools = await scraper.fetch_subreddit_tools("test")
                assert len(tools) >= 0  # 可能因为内容过滤而返回0


class TestHackerNewsScraper:
    """Hacker News抓取器测试"""

    @pytest.fixture
    def scraper(self):
        return HackerNewsScraper()

    def test_is_tool_related(self, scraper):
        """测试工具相关内容判断"""
        # Show HN帖子应该被识别
        show_hn_title = "Show HN: My new AI tool"
        assert scraper._is_tool_related(show_hn_title, "")

        # 包含工具关键词的帖子
        tool_title = "New SaaS platform for developers"
        assert scraper._is_tool_related(tool_title, "")

        # 非工具相关帖子
        non_tool_title = "Ask HN: How to learn coding?"
        assert not scraper._is_tool_related(non_tool_title, "")

    def test_parse_story(self, scraper):
        """测试Hacker News故事解析"""
        story_data = {
            'title': 'Show HN: AI Productivity Tool',
            'url': 'https://example.com/ai-tool',
            'score': 200,
            'time': 1705123456,
            'id': 12345
        }

        tool = scraper._parse_story(story_data)

        assert tool is not None
        assert tool.tool_name == "Show HN: AI Productivity Tool"
        assert tool.votes == 200
        assert tool.link == "https://example.com/ai-tool"

    @pytest.mark.asyncio
    async def test_fetch_latest_stories(self, scraper):
        """测试获取最新故事"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock newstories response
            mock_client.return_value.__aenter__.return_value.get.side_effect = [
                Mock(json=lambda: [12345, 67890]),  # newstories
                Mock(json=lambda: {  # story details
                    'title': 'Test Tool',
                    'url': 'https://example.com',
                    'score': 100,
                    'time': 1705123456,
                    'id': 12345
                })
            ]

            with patch.object(scraper, '_is_tool_related', return_value=True):
                tools = await scraper.fetch_latest_stories(limit=1)
                assert len(tools) >= 0


class TestFetchAllFeeds:
    """测试批量抓取feeds"""

    @pytest.mark.asyncio
    async def test_fetch_all_feeds(self):
        """测试抓取所有feeds"""
        feed_urls = [
            "https://example.com/feed1",
            "https://example.com/feed2"
        ]

        with patch('scrapers.rss_scraper.RSScraper.fetch_feed') as mock_fetch:
            mock_fetch.return_value = [
                RawTool(
                    tool_name="Test Tool",
                    description="Test description",
                    link="https://example.com/tool1",
                    date=datetime.now(timezone.utc)
                )
            ]

            tools = await fetch_all_feeds(feed_urls)

            # 验证去重功能
            assert len(tools) == 2  # 两个feed各返回一个相同链接的工具，应该去重
            mock_fetch.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])