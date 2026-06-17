"""
数据采集器工厂
统一管理所有数据采集器，提供单一入口
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
from loguru import logger

from .collectors.baostock_collector import BaostockCollector
from .collectors.akshare_collector import AkshareCollector
from .collectors.macro_collector import MacroCollector
from .industry_pe_pb_calculator import IndustryPEPBHistoryCalculator
from .industry_mapper import IndustryMapper, IndustryMapping
from .data_cache import DataCache


@dataclass
class IndustryData:
    """行业完整数据结构"""
    name: str                           # 业务行业名称
    sw_code: str                         # 申万行业代码
    baostock_code: str                   # Baostock 行业代码

    # 当前数据
    current_price: Optional[float] = None
    current_pe: Optional[float] = None
    current_pb: Optional[float] = None
    pe_percentile: Optional[float] = None
    pb_percentile: Optional[float] = None

    # 趋势数据
    price_trend: Optional[str] = None
    price_change_pct: Optional[float] = None
    valuation_trend: Optional[str] = None

    # 历史分位
    percentile_data: Optional[Dict] = None

    # 背离信号
    divergence_signal: Optional[Dict] = None

    # 元数据
    update_time: Optional[datetime] = None
    benchmarks: List[str] = field(default_factory=list)

    # 原始数据
    raw_pe_pb_data: Optional[Dict] = None
    raw_index_history: Optional[pd.DataFrame] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        result = {
            'name': self.name,
            'sw_code': self.sw_code,
            'baostock_code': self.baostock_code,
            'current_price': self.current_price,
            'current_pe': self.current_pe,
            'current_pb': self.current_pb,
            'pe_percentile': self.pe_percentile,
            'pb_percentile': self.pb_percentile,
            'price_trend': self.price_trend,
            'price_change_pct': self.price_change_pct,
            'valuation_trend': self.valuation_trend,
            'benchmarks': self.benchmarks,
            'update_time': self.update_time.isoformat() if self.update_time else None,
        }

        if self.divergence_signal:
            result['divergence_signal'] = self.divergence_signal.get('背离信号')

        return result


class DataCollector:
    """
    统一数据采集器

    整合 Baostock、Akshare、宏观数据采集器
    提供单一入口获取所有行业数据
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        cache_enabled: bool = True,
        cache_ttl_hours: int = 24
    ):
        """
        初始化数据采集器

        Args:
            config_path: 配置文件路径
            cache_enabled: 是否启用缓存
            cache_ttl_hours: 缓存过期时间
        """
        # 初始化采集器
        self._baostock = BaostockCollector()
        self._akshare = AkshareCollector()
        self._macro = MacroCollector(akshare_collector=self._akshare)

        # 初始化计算器
        self._calculator = IndustryPEPBHistoryCalculator(
            akshare_collector=self._akshare,
            baostock_collector=self._baostock
        )

        # 初始化行业映射
        self._mapper = IndustryMapper(config_path=config_path)

        # 初始化缓存
        self._cache = DataCache(ttl_hours=cache_ttl_hours) if cache_enabled else None
        self._cache_enabled = cache_enabled

        # 连接状态
        self._connected = False

    def connect(self) -> bool:
        """连接所有数据源"""
        logger.info("开始连接数据源...")

        # 连接 Baostock
        if not self._baostock.connect():
            logger.error("Baostock 连接失败")
            return False

        # 连接 Akshare
        if not self._akshare.connect():
            logger.error("Akshare 连接失败")
            self._baostock.disconnect()
            return False

        # 连接宏观数据采集器
        if not self._macro.connect():
            logger.warning("宏观数据采集器连接失败，部分功能可能不可用")

        self._connected = True
        logger.info("所有数据源连接成功")
        return True

    def disconnect(self) -> None:
        """断开所有数据源"""
        self._baostock.disconnect()
        self._akshare.disconnect()
        self._macro.disconnect()
        self._calculator.disconnect()
        self._connected = False
        logger.info("所有数据源已断开")

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected

    def collect_industry(self, industry_name: str) -> Optional[IndustryData]:
        """
        采集指定行业的完整数据

        Args:
            industry_name: 业务行业名称

        Returns:
            IndustryData 或 None
        """
        # 检查缓存
        if self._cache_enabled:
            cached = self._cache.get("industry", industry_name)
            if cached:
                logger.info(f"从缓存获取行业数据: {industry_name}")
                return self._deserialize_industry_data(cached)

        # 获取行业映射
        mapping = self._mapper.get_mapping(industry_name)
        if not mapping:
            logger.error(f"未找到行业映射: {industry_name}")
            return None

        logger.info(f"开始采集行业数据: {industry_name}")

        # 创建行业数据对象
        data = IndustryData(
            name=mapping.name,
            sw_code=mapping.sw_index_code,
            baostock_code=mapping.baostock_code,
            benchmarks=mapping.benchmarks,
            update_time=datetime.now(),
        )

        try:
            # 1. 获取当前 PE/PB
            pe_pb_data = self._calculator.get_current_pe_pb(mapping.sw_index_code)
            if pe_pb_data:
                data.current_pe = pe_pb_data.get('pe_ttm')
                data.current_pb = pe_pb_data.get('pb')
                data.raw_pe_pb_data = pe_pb_data

            # 2. 计算分位
            percentile_data = self._calculator.calculate_pe_pb_percentile(mapping.sw_index_code)
            if percentile_data:
                data.pe_percentile = percentile_data.get('点位分位')
                data.percentile_data = percentile_data

            # 3. 获取趋势
            price_trend = self._calculator.get_trend(mapping.sw_index_code, window=12)
            if price_trend:
                data.price_trend = price_trend.get('趋势')
                data.price_change_pct = price_trend.get('窗口变化率')

            valuation_trend = self._calculator.get_trend(mapping.sw_index_code, window=12)
            if valuation_trend:
                data.valuation_trend = valuation_trend.get('趋势')

            # 4. 获取背离信号
            divergence = self._calculator.get_divergence_signal(mapping.sw_index_code)
            if divergence:
                data.divergence_signal = divergence

            # 缓存结果
            if self._cache_enabled:
                self._cache.set(self._serialize_industry_data(data), "industry", industry_name)

            logger.info(f"行业数据采集完成: {industry_name}")

        except Exception as e:
            logger.error(f"采集行业 {industry_name} 数据失败: {e}")

        return data

    def collect_all_industries(self) -> List[IndustryData]:
        """
        采集所有目标行业的数据

        Returns:
            所有行业的 IndustryData 列表
        """
        results = []
        names = self._mapper.get_all_names()

        logger.info(f"开始采集 {len(names)} 个行业的数据...")

        for name in names:
            try:
                data = self.collect_industry(name)
                if data:
                    results.append(data)
            except Exception as e:
                logger.error(f"采集行业 {name} 失败: {e}")

        logger.info(f"行业数据采集完成: {len(results)}/{len(names)} 个成功")
        return results

    def collect_macro(self) -> Dict[str, Any]:
        """
        采集宏观数据

        Returns:
            宏观数据字典
        """
        if self._cache_enabled:
            cached = self._cache.get("macro", "all")
            if cached:
                logger.info("从缓存获取宏观数据")
                return cached

        logger.info("开始采集宏观数据...")

        try:
            latest_macro = self._macro.get_latest_macro()
            all_macro = self._macro.get_all_macro_data()

            result = {
                'latest': latest_macro,
                'historical': all_macro,
                'update_time': datetime.now().isoformat(),
            }

            if self._cache_enabled:
                self._cache.set(result, "macro", "all")

            return result

        except Exception as e:
            logger.error(f"采集宏观数据失败: {e}")
            return {}

    def get_sw_industry_list(self) -> pd.DataFrame:
        """
        获取申万二级行业完整列表

        Returns:
            申万行业 DataFrame
        """
        return self._akshare.get_sw_index_second_info()

    def get_baostock_industry_list(self) -> pd.DataFrame:
        """
        获取 Baostock 行业分类

        Returns:
            Baostock 行业分类 DataFrame
        """
        return self._baostock.get_stock_industry()

    def _serialize_industry_data(self, data: IndustryData) -> Dict:
        """序列化 IndustryData"""
        return data.to_dict()

    def _deserialize_industry_data(self, data: Dict) -> IndustryData:
        """反序列化 IndustryData"""
        return IndustryData(
            name=data['name'],
            sw_code=data['sw_code'],
            baostock_code=data['baostock_code'],
            current_price=data.get('current_price'),
            current_pe=data.get('current_pe'),
            current_pb=data.get('current_pb'),
            pe_percentile=data.get('pe_percentile'),
            pb_percentile=data.get('pb_percentile'),
            price_trend=data.get('price_trend'),
            price_change_pct=data.get('price_change_pct'),
            valuation_trend=data.get('valuation_trend'),
            benchmarks=data.get('benchmarks', []),
            update_time=datetime.fromisoformat(data['update_time']) if data.get('update_time') else None,
        )

    def clear_cache(self) -> None:
        """清空缓存"""
        if self._cache:
            self._cache.clear()
            logger.info("缓存已清空")

    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        if self._cache:
            return self._cache.get_stats()
        return {}
