"""
阶段一验证脚本
验证基础设施搭建是否完成
"""

import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def verify_infrastructure():
    """验证基础设施"""

    print("=" * 60)
    print("阶段一：基础设施搭建 - 验证报告")
    print("=" * 60)

    errors = []

    # 1. 验证目录结构
    print("\n[1/5] 验证目录结构...")
    required_dirs = [
        "config",
        "src",
        "src/data",
        "src/analysis",
        "src/output",
        "logs",
        "tests",
        "data",
        "reports",
    ]

    for d in required_dirs:
        path = Path(d)
        if path.exists() and path.is_dir():
            print(f"  ✓ {d}/")
        else:
            print(f"  ✗ {d}/ 缺失")
            errors.append(f"目录 {d} 不存在")

    # 2. 验证配置文件
    print("\n[2/5] 验证配置文件...")
    config_file = Path("config/config.yaml")
    if config_file.exists():
        import yaml
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        print(f"  ✓ config/config.yaml")
        print(f"    - 项目名称: {config['project']['name']}")
        print(f"    - 目标行业: {len(config['industries']['target_industries'])} 个")
        print(f"    - 历史数据: {config['data_params']['history_years']} 年")
    else:
        print(f"  ✗ config/config.yaml 缺失")
        errors.append("配置文件不存在")

    # 3. 验证依赖
    print("\n[3/5] 验证依赖...")
    deps = [
        ("akshare", "数据获取"),
        ("baostock", "数据获取"),
        ("pandas", "数据处理"),
        ("numpy", "数值计算"),
        ("loguru", "日志"),
        ("yaml", "配置解析"),
    ]

    for dep, desc in deps:
        try:
            mod = __import__(dep)
            ver = getattr(mod, '__version__', 'unknown')
            print(f"  ✓ {dep} ({desc}): {ver}")
        except ImportError:
            print(f"  ✗ {dep} ({desc}): 未安装")
            errors.append(f"依赖 {dep} 未安装")

    # 4. 验证日志模块
    print("\n[4/5] 验证日志模块...")
    try:
        from config.logger import setup_logger, get_logger
        logger = setup_logger('INFO')
        log = get_logger('verify')
        log.info("日志模块工作正常")
        print("  ✓ config/logger.py")
    except Exception as e:
        print(f"  ✗ 日志模块错误: {e}")
        errors.append(str(e))

    # 5. 验证 requirements.txt
    print("\n[5/5] 验证 requirements.txt...")
    req_file = Path("requirements.txt")
    if req_file.exists():
        lines = req_file.read_text(encoding='utf-8').strip().split('\n')
        # 过滤注释和空行
        deps_list = [l for l in lines if l and not l.startswith('#')]
        print(f"  ✓ requirements.txt ({len(deps_list)} 个依赖)")
    else:
        print(f"  ✗ requirements.txt 缺失")
        errors.append("requirements.txt 不存在")

    # 总结
    print("\n" + "=" * 60)
    if errors:
        print("验证结果: 有错误")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print("验证结果: 全部通过 ✓")
        return True


if __name__ == "__main__":
    success = verify_infrastructure()
    sys.exit(0 if success else 1)
