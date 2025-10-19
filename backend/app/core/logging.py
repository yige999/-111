import logging
import sys
from .config import settings


def setup_logging():
    """设置日志配置"""

    # 创建日志格式器
    formatter = logging.Formatter(settings.LOG_FORMAT)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # 文件处理器（可选）
    # file_handler = logging.FileHandler('app.log')
    # file_handler.setFormatter(formatter)

    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.addHandler(console_handler)
    # root_logger.addHandler(file_handler)

    # 禁用一些库的详细日志
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)