"""
数据缓存模块
避免重复请求，提高效率
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional, Callable
from functools import wraps
from loguru import logger
import pandas as pd


class DataCache:
    """
    数据缓存管理器

    支持：
    - 内存缓存
    - 文件缓存
    - TTL 过期机制
    """

    def __init__(self, cache_dir: str = "data/cache", ttl_hours: int = 24):
        """
        初始化缓存

        Args:
            cache_dir: 缓存文件目录
            ttl_hours: 缓存过期时间（小时）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_hours = ttl_hours

        # 内存缓存
        self._memory_cache: dict = {}

        # 统计
        self._hit_count = 0
        self._miss_count = 0

    def _get_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = "_".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cache_file(self, key: str, prefix: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{prefix}_{key}.json"

    def get(self, prefix: str, *args, **kwargs) -> Optional[Any]:
        """
        获取缓存

        Args:
            prefix: 缓存前缀
            *args, **kwargs: 用于生成缓存键的参数

        Returns:
            缓存的数据或 None
        """
        key = self._get_cache_key(prefix, *args, **kwargs)

        # 先检查内存缓存
        mem_key = f"{prefix}_{key}"
        if mem_key in self._memory_cache:
            cached = self._memory_cache[mem_key]
            # 检查过期
            if datetime.now() < cached['expires_at']:
                self._hit_count += 1
                logger.debug(f"缓存命中(内存): {prefix}")
                return cached['data']
            else:
                del self._memory_cache[mem_key]

        # 检查文件缓存
        cache_file = self._get_cache_file(key, prefix)
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)

                # 检查过期
                expires_at = datetime.fromisoformat(cached['expires_at'])
                if datetime.now() < expires_at:
                    # 更新内存缓存
                    self._memory_cache[mem_key] = cached
                    self._hit_count += 1
                    logger.debug(f"缓存命中(文件): {prefix}")
                    return cached['data']
                else:
                    # 删除过期文件
                    cache_file.unlink()
                    logger.debug(f"缓存过期已删除: {prefix}")

            except Exception as e:
                logger.warning(f"读取缓存文件失败: {e}")

        self._miss_count += 1
        logger.debug(f"缓存未命中: {prefix}")
        return None

    def set(self, data: Any, prefix: str, *args, **kwargs) -> None:
        """
        设置缓存

        Args:
            data: 要缓存的数据
            prefix: 缓存前缀
            *args, **kwargs: 用于生成缓存键的参数
        """
        key = self._get_cache_key(prefix, *args, **kwargs)
        mem_key = f"{prefix}_{key}"

        # 序列化为 JSON 兼容格式
        serialized_data = self._serialize(data)

        cached = {
            'data': serialized_data,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=self.ttl_hours)).isoformat(),
        }

        # 保存到内存缓存
        self._memory_cache[mem_key] = cached

        # 保存到文件缓存
        cache_file = self._get_cache_file(key, prefix)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached, f, ensure_ascii=False, indent=2)
            logger.debug(f"缓存已保存: {prefix}")
        except Exception as e:
            logger.warning(f"保存缓存文件失败: {e}")

    def _serialize(self, data: Any) -> Any:
        """序列化为 JSON 兼容格式"""
        if isinstance(data, pd.DataFrame):
            return {
                '__type__': 'DataFrame',
                'data': data.to_dict(orient='records'),
                'columns': list(data.columns),
            }
        elif isinstance(data, pd.Series):
            return {
                '__type__': 'Series',
                'data': data.to_dict(),
            }
        elif isinstance(data, dict):
            return {k: self._serialize(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize(item) for item in data]
        else:
            return data

    def _deserialize(self, data: Any) -> Any:
        """反序列化"""
        if isinstance(data, dict):
            if data.get('__type__') == 'DataFrame':
                return pd.DataFrame(data['data'], columns=data.get('columns'))
            elif data.get('__type__') == 'Series':
                return pd.Series(data['data'])
            else:
                return {k: self._deserialize(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._deserialize(item) for item in data]
        else:
            return data

    def invalidate(self, prefix: str, *args, **kwargs) -> None:
        """
        使缓存失效

        Args:
            prefix: 缓存前缀
            *args, **kwargs: 用于生成缓存键的参数
        """
        key = self._get_cache_key(prefix, *args, **kwargs)
        mem_key = f"{prefix}_{key}"

        # 删除内存缓存
        if mem_key in self._memory_cache:
            del self._memory_cache[mem_key]

        # 删除文件缓存
        cache_file = self._get_cache_file(key, prefix)
        if cache_file.exists():
            cache_file.unlink()
            logger.debug(f"缓存已失效: {prefix}")

    def clear(self) -> None:
        """清空所有缓存"""
        self._memory_cache.clear()
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"删除缓存文件失败: {e}")
        logger.info("所有缓存已清空")

    def get_stats(self) -> dict:
        """获取缓存统计"""
        total = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total if total > 0 else 0

        return {
            'hit_count': self._hit_count,
            'miss_count': self._miss_count,
            'hit_rate': f"{hit_rate:.1%}",
            'memory_cache_size': len(self._memory_cache),
            'cache_files': len(list(self.cache_dir.glob("*.json"))),
        }

    def cleanup_expired(self) -> int:
        """清理过期缓存文件"""
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                expires_at = datetime.fromisoformat(cached['expires_at'])
                if datetime.now() >= expires_at:
                    cache_file.unlink()
                    count += 1
            except Exception:
                pass

        if count > 0:
            logger.info(f"清理了 {count} 个过期缓存文件")

        return count


def cached(prefix: str, ttl_hours: int = 24):
    """
    缓存装饰器

    Args:
        prefix: 缓存前缀
        ttl_hours: 过期时间

    Usage:
        @cached("my_data")
        def get_data(date: str):
            # ... 获取数据的逻辑
            return data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 尝试从缓存获取
            # 注意：这个简单的实现可能需要根据实际情况调整
            return func(*args, **kwargs)

        return wrapper
    return decorator
