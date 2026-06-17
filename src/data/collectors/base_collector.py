"""
数据采集器基类
定义统一的接口规范
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
from datetime import datetime
import time
from loguru import logger


class BaseCollector(ABC):
    """数据采集器基类"""

    # 重试配置
    DEFAULT_RETRY = 3
    DEFAULT_RETRY_INTERVAL = 2  # 秒

    def __init__(self, retry: int = DEFAULT_RETRY, retry_interval: int = DEFAULT_RETRY_INTERVAL):
        """
        初始化采集器

        Args:
            retry: 最大重试次数
            retry_interval: 重试间隔（秒）
        """
        self.retry = retry
        self.retry_interval = retry_interval
        self.last_error: Optional[str] = None

    @abstractmethod
    def connect(self) -> bool:
        """
        连接数据源

        Returns:
            连接是否成功
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """断开数据源连接"""
        pass

    def _retry_wrapper(self, func, *args, **kwargs) -> Any:
        """
        带重试的函数调用包装器

        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数返回值

        Raises:
            最后一次重试的错误
        """
        last_exception = None

        for attempt in range(self.retry + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                self.last_error = str(e)

                if attempt < self.retry:
                    logger.warning(
                        f"{self.__class__.__name__}: {func.__name__} 失败，"
                        f"尝试 {attempt + 1}/{self.retry + 1}，"
                        f"错误: {e}，{self.retry_interval}秒后重试..."
                    )
                    time.sleep(self.retry_interval)
                else:
                    logger.error(
                        f"{self.__class__.__name__}: {func.__name__} "
                        f"重试 {self.retry + 1} 次后仍然失败"
                    )

        raise last_exception

    def is_connected(self) -> bool:
        """检查是否已连接"""
        raise NotImplementedError
