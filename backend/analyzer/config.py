"""
分析器配置 - 窗口4
管理OpenAI API设置和分析参数
"""

import os
from typing import Optional

class AnalyzerConfig:
    """分析器配置类"""

    def __init__(self):
        # OpenAI配置
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o')

        # 分析参数
        self.max_tools_per_batch = int(os.getenv('MAX_TOOLS_PER_BATCH', '10'))
        self.temperature = float(os.getenv('ANALYSIS_TEMPERATURE', '0.3'))
        self.max_tokens = int(os.getenv('MAX_TOKENS', '4000'))

        # 成本控制
        self.daily_token_limit = int(os.getenv('DAILY_TOKEN_LIMIT', '100000'))
        self.daily_cost_limit = float(os.getenv('DAILY_COST_LIMIT', '5.0'))

        # 降级配置
        self.enable_fallback = os.getenv('ENABLE_FALLBACK', 'true').lower() == 'true'
        self.retry_attempts = int(os.getenv('RETRY_ATTEMPTS', '3'))
        self.retry_delay = float(os.getenv('RETRY_DELAY', '1.0'))

    def validate(self) -> bool:
        """验证配置有效性"""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY 环境变量未设置")

        if self.max_tools_per_batch <= 0:
            raise ValueError("MAX_TOOLS_PER_BATCH 必须大于0")

        if not (0 <= self.temperature <= 2):
            raise ValueError("ANALYSIS_TEMPERATURE 必须在0-2之间")

        return True

    def get_openai_config(self) -> dict:
        """获取OpenAI配置"""
        return {
            'api_key': self.openai_api_key,
            'model': self.openai_model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }

# 全局配置实例
config = AnalyzerConfig()