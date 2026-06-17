"""
数据采集器模块
"""

from .base_collector import BaseCollector
from .baostock_collector import BaostockCollector
from .akshare_collector import AkshareCollector
from .macro_collector import MacroCollector

__all__ = [
    'BaseCollector',
    'BaostockCollector',
    'AkshareCollector',
    'MacroCollector',
]
