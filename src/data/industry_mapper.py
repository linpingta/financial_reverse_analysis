"""
行业映射模块
管理业务行业与数据源行业代码的映射关系
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from loguru import logger

import yaml
from pathlib import Path


@dataclass
class IndustryMapping:
    """单个行业的映射配置"""
    name: str                           # 业务行业名称
    baostock_code: str                  # Baostock 行业分类代码
    sw_index_code: str                  # 申万二级行业代码
    benchmarks: List[str] = field(default_factory=list)  # 跟踪的景气指标


class IndustryMapper:
    """
    行业映射管理器

    管理业务定义的行业与 Baostock/申万行业代码的映射关系
    """

    # 默认的行业映射（10个强周期行业）
    DEFAULT_MAPPINGS = [
        {
            "name": "航空机场",
            "baostock_code": "G56",  # 航空运输业
            "sw_index_code": "801991.SI",
            "benchmarks": ["旅客周转量", "客座率", "航油价格"],
        },
        {
            "name": "生猪养殖",
            "baostock_code": "A03",  # 畜牧业
            "sw_index_code": "801017.SI",
            "benchmarks": ["能繁母猪存栏量", "生猪价格", "猪粮比"],
        },
        {
            "name": "基础化工",
            "baostock_code": "C26",  # 化学原料和化学制品制造业
            "sw_index_code": "801033.SI",
            "benchmarks": ["化工品价格指数", "开工率", "库存周期"],
        },
        {
            "name": "煤炭",
            "baostock_code": "B06",  # 煤炭开采和洗选业
            "sw_index_code": "801951.SI",
            "benchmarks": ["秦皇岛煤价指数", "港口库存", "发电量"],
        },
        {
            "name": "有色金属",
            "baostock_code": "C32",  # 有色金属冶炼和压延加工业
            "sw_index_code": "801055.SI",
            "benchmarks": ["LME铜价", "库存变化", "加工费"],
        },
        {
            "name": "远洋航运",
            "baostock_code": "G55",  # 水上运输业
            "sw_index_code": "801992.SI",
            "benchmarks": ["BDI指数", "集装箱运价", "新船订单"],
        },
        {
            "name": "酒店旅游",
            "baostock_code": "H61",  # 住宿业
            "sw_index_code": "801219.SI",
            "benchmarks": ["出游人数", "酒店入住率", "旅游收入"],
        },
        {
            "name": "周期半导体",
            "baostock_code": "C39",  # 电子设备制造业
            "sw_index_code": "801081.SI",
            "benchmarks": ["全球半导体销售额", "存储芯片价格"],
        },
        {
            "name": "光伏上游",
            "baostock_code": "C38",  # 电气机械和器材制造业
            "sw_index_code": "801735.SI",
            "benchmarks": ["硅料价格", "组件价格", "装机量"],
        },
        {
            "name": "工程机械",
            "baostock_code": "C35",  # 专用设备制造业
            "sw_index_code": "801077.SI",
            "benchmarks": ["挖掘机销量", "小松开工小时数", "房地产新开工"],
        },
    ]

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化行业映射

        Args:
            config_path: 配置文件路径，如不提供则使用默认映射
        """
        self._mappings: Dict[str, IndustryMapping] = {}
        self._sw_code_to_name: Dict[str, str] = {}
        self._baostock_code_to_name: Dict[str, str] = {}

        if config_path:
            self._load_from_config(config_path)
        else:
            self._load_default_mappings()

    def _load_from_config(self, config_path: str) -> None:
        """从配置文件加载行业映射"""
        try:
            path = Path(config_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                industries = config.get('industries', {}).get('target_industries', [])
                for ind in industries:
                    mapping = IndustryMapping(
                        name=ind['name'],
                        baostock_code=ind.get('baostock_code', ''),
                        sw_index_code=ind.get('sw_index_code', ''),
                        benchmarks=ind.get('benchmarks', []),
                    )
                    self._add_mapping(mapping)

                logger.info(f"从配置文件加载了 {len(self._mappings)} 个行业映射")
            else:
                logger.warning(f"配置文件不存在: {config_path}，使用默认映射")
                self._load_default_mappings()

        except Exception as e:
            logger.error(f"加载行业配置失败: {e}，使用默认映射")
            self._load_default_mappings()

    def _load_default_mappings(self) -> None:
        """加载默认行业映射"""
        for ind in self.DEFAULT_MAPPINGS:
            mapping = IndustryMapping(
                name=ind['name'],
                baostock_code=ind['baostock_code'],
                sw_index_code=ind['sw_index_code'],
                benchmarks=ind['benchmarks'],
            )
            self._add_mapping(mapping)

        logger.info(f"加载了 {len(self._mappings)} 个默认行业映射")

    def _add_mapping(self, mapping: IndustryMapping) -> None:
        """添加单个映射"""
        self._mappings[mapping.name] = mapping
        self._sw_code_to_name[mapping.sw_index_code] = mapping.name
        self._baostock_code_to_name[mapping.baostock_code] = mapping.name

    def get_mapping(self, name: str) -> Optional[IndustryMapping]:
        """
        根据业务名称获取映射

        Args:
            name: 业务行业名称

        Returns:
            IndustryMapping 或 None
        """
        return self._mappings.get(name)

    def get_sw_code(self, name: str) -> Optional[str]:
        """获取申万行业代码"""
        mapping = self.get_mapping(name)
        return mapping.sw_index_code if mapping else None

    def get_baostock_code(self, name: str) -> Optional[str]:
        """获取 Baostock 行业代码"""
        mapping = self.get_mapping(name)
        return mapping.baostock_code if mapping else None

    def get_all_names(self) -> List[str]:
        """获取所有业务行业名称"""
        return list(self._mappings.keys())

    def get_all_sw_codes(self) -> List[str]:
        """获取所有申万行业代码"""
        return [m.sw_index_code for m in self._mappings.values()]

    def get_all_baostock_codes(self) -> List[str]:
        """获取所有 Baostock 行业代码"""
        return [m.baostock_code for m in self._mappings.values()]

    def get_by_sw_code(self, sw_code: str) -> Optional[IndustryMapping]:
        """根据申万代码获取映射"""
        name = self._sw_code_to_name.get(sw_code)
        return self.get_mapping(name) if name else None

    def get_by_baostock_code(self, bs_code: str) -> Optional[IndustryMapping]:
        """根据 Baostock 代码获取映射"""
        name = self._baostock_code_to_name.get(bs_code)
        return self.get_mapping(name) if name else None

    def get_all_mappings(self) -> List[IndustryMapping]:
        """获取所有映射"""
        return list(self._mappings.values())

    def to_dict_list(self) -> List[Dict]:
        """转换为字典列表（用于配置导出）"""
        return [
            {
                "name": m.name,
                "baostock_code": m.baostock_code,
                "sw_index_code": m.sw_index_code,
                "benchmarks": m.benchmarks,
            }
            for m in self._mappings.values()
        ]

    def add_mapping(self, mapping: IndustryMapping) -> None:
        """添加新的行业映射"""
        self._add_mapping(mapping)
        logger.info(f"添加行业映射: {mapping.name} -> {mapping.sw_index_code}")

    def remove_mapping(self, name: str) -> bool:
        """移除行业映射"""
        if name in self._mappings:
            mapping = self._mappings[name]
            del self._sw_code_to_name[mapping.sw_index_code]
            del self._baostock_code_to_name[mapping.baostock_code]
            del self._mappings[name]
            logger.info(f"移除行业映射: {name}")
            return True
        return False

    def summary(self) -> str:
        """获取映射摘要"""
        lines = ["行业映射摘要:"]
        for mapping in self._mappings.values():
            lines.append(f"  - {mapping.name}: 申万 {mapping.sw_index_code}, Baostock {mapping.baostock_code}")
        return "\n".join(lines)
