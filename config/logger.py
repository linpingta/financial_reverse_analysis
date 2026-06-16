"""
日志配置模块
基于 loguru

使用方法:
    from config.logger import setup_logger, get_logger
    logger = setup_logger('INFO')
"""

import sys
from pathlib import Path
from loguru import logger as _logger

# 获取项目根目录（config/ 的上级）
_current_file = Path(__file__).resolve()
_config_dir = _current_file.parent
PROJECT_ROOT = _config_dir.parent

# 日志目录
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 日志文件配置
LOG_FILE = LOG_DIR / "app.log"

# 日志格式
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# 简化的控制台格式
CONSOLE_FORMAT = (
    "<green>{time:HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<level>{message}</level>"
)


def setup_logger(level: str = "INFO"):
    """
    配置日志系统

    Args:
        level: 日志级别 (DEBUG / INFO / WARNING / ERROR)
    """
    # 移除默认处理器
    _logger.remove()

    # 添加控制台输出（INFO及以上级别）
    _logger.add(
        sys.stderr,
        format=CONSOLE_FORMAT,
        level=level,
        colorize=True,
    )

    # 添加文件输出（DEBUG级别，保留所有日志）
    _logger.add(
        LOG_FILE,
        format=LOG_FORMAT,
        level="DEBUG",
        rotation="100 MB",  # 单文件超过100MB时轮转
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        enqueue=True,  # 异步写入，避免阻塞
    )

    return _logger


def get_logger(name: str = None):
    """
    获取日志记录器

    Args:
        name: 模块名称，将显示在日志中

    Returns:
        logger instance
    """
    if name:
        return _logger.bind(name=name)
    return _logger


# 预配置的默认 logger
default_logger = setup_logger()
