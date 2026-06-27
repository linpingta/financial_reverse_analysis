# -*- coding: utf-8 -*-
"""
辅助函数模块
"""
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import sys


def get_industries_list() -> List[str]:
    """
    获取行业列表
    
    Returns:
        行业名称列表
    """
    try:
        from src.data.industry_mapper import IndustryMapper
        mapper = IndustryMapper()
        return list(mapper.industry_mapping.keys())
    except Exception:
        return [
            "航空机场",
            "生猪养殖",
            "光伏设备",
            "锂电池",
            "半导体",
            "白酒",
            "银行",
            "保险",
            "证券",
            "房地产"
        ]


def format_datetime(dt: Optional[datetime], fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    格式化日期时间
    
    Args:
        dt: datetime对象
        fmt: 格式字符串
        
    Returns:
        格式化后的字符串
    """
    if dt is None:
        return ''
    return dt.strftime(fmt)


def format_percentage(value: Optional[float]) -> str:
    """
    格式化百分比
    
    Args:
        value: 数值（0-100）
        
    Returns:
        格式化后的字符串
    """
    if value is None:
        return '-'
    return f'{value:.2f}%'


def get_project_root() -> Path:
    """
    获取项目根目录
    
    Returns:
        项目根目录路径
    """
    current_file = Path(__file__)
    return current_file.parent.parent.parent.parent


def ensure_dir(path: Path):
    """
    确保目录存在
    
    Args:
        path: 目录路径
    """
    path.mkdir(parents=True, exist_ok=True)


def safe_float(value, default=0.0) -> float:
    """
    安全转换为浮点数
    
    Args:
        value: 要转换的值
        default: 默认值
        
    Returns:
        转换后的浮点数
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0) -> int:
    """
    安全转换为整数
    
    Args:
        value: 要转换的值
        default: 默认值
        
    Returns:
        转换后的整数
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default