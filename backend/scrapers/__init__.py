# RSS Scrapers Module - 窗口2：RSS 抓取模块

# 专用抓取器
from .producthunt_scraper import ProductHuntScraper, fetch_producthunt_tools
from .futurepedia_scraper import FuturepediaScraper, fetch_futurepedia_tools

# 数据处理
from .data_cleaner import DataCleaner, clean_and_validate_tools

# 统一管理器
from .rss_manager import RSSManager, rss_manager, fetch_ai_tools_from_rss, get_rss_sources_info

# 通用抓取器（原有）
from .rss_scraper import RSScraper, fetch_all_feeds
from .reddit_scraper import RedditScraper, fetch_reddit_tools
from .hackernews_scraper import HackerNewsScraper, fetch_hackernews_tools

__all__ = [
    # 专用抓取器
    'ProductHuntScraper', 'fetch_producthunt_tools',
    'FuturepediaScraper', 'fetch_futurepedia_tools',

    # 数据处理
    'DataCleaner', 'clean_and_validate_tools',

    # 统一管理器
    'RSSManager', 'rss_manager', 'fetch_ai_tools_from_rss', 'get_rss_sources_info',

    # 通用抓取器
    'RSScraper', 'fetch_all_feeds',
    'RedditScraper', 'fetch_reddit_tools',
    'HackerNewsScraper', 'fetch_hackernews_tools'
]
