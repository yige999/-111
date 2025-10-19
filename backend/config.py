from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # OpenAI API
    openai_api_key: str
    openai_model: str = "gpt-4o"

    # Supabase
    supabase_url: str
    supabase_key: str

    # 数据源配置
    rss_feeds: str = "https://www.producthunt.com/feed,https://www.futurepedia.io/new"
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None

    # 调度配置
    cron_schedule: str = "0 9 * * *"
    data_source_limit: int = 50

    # API配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    @property
    def rss_feeds_list(self) -> List[str]:
        return [feed.strip() for feed in self.rss_feeds.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()