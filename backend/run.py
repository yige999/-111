#!/usr/bin/env python3
"""
AutoSaaS Radar 后端启动脚本
"""

import uvicorn
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """启动FastAPI服务器"""
    logger.info("正在启动 AutoSaaS Radar 后端服务...")
    logger.info(f"服务地址: http://{settings.api_host}:{settings.api_port}")
    logger.info(f"调试模式: {settings.debug}")

    try:
        uvicorn.run(
            "app:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.debug,
            log_level="info" if not settings.debug else "debug"
        )
    except KeyboardInterrupt:
        logger.info("服务已停止")
    except Exception as e:
        logger.error(f"启动服务失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()