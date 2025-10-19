import os
from typing import List, Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "AutoSaaS Radar"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API 配置
    API_V1_STR: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # OpenAI 配置
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_TEMPERATURE: float = 0.1

    # Supabase 配置
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # 数据源配置
    RSS_FEEDS: List[str] = [
        "https://www.producthunt.com/feed",
        "https://www.futurepedia.io/feed",
        "https://news.ycombinator.com/rss"
    ]

    # Reddit 配置
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: str = "AutoSaaS-Radar/1.0"

    # 调度配置
    CRON_SCHEDULE: str = "0 9 * * *"  # 每天上午9点
    DATA_SOURCE_LIMIT: int = 50
    ANALYSIS_BATCH_SIZE: int = 10

    # 缓存配置
    CACHE_TTL: int = 3600  # 1小时
    REDIS_URL: Optional[str] = None

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @validator("ALLOWED_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError("ALLOWED_ORIGINS must be a string or list")

    @validator("RSS_FEEDS", pre=True)
    def assemble_rss_feeds(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError("RSS_FEEDS must be a string or list")

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局设置实例
settings = Settings()