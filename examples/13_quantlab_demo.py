"""
finquant - QuantLab 完整示例

演示量化研究实验室的完整使用流程：
1. 加载数据
2. 计算因子
3. 因子研究（IC分析、分组回测、相关性）
4. 策略回测
5. 参数优化
6. 策略对比
"""

import pandas as pd
import numpy as np


def example_full_workflow():
    """完整工作流程示例"""
    print("\n" + "="*70)
    print("QuantLab 完整工作流程")
    print("="*70)

    from finquant.research import QuantLab, create_lab
    from finquant.strategy import MAStrategy

    # 创建实验室
    lab = create_lab(name="DemoLab", initial_capital=1000000)

    # ========== 1. 加载数据 ==========
    print("\n[步骤1] 加载数据")
    print("-" * 50)

    codes = [
        "SH600519",  # 茅台
        "SH600036",  # 招商银行
        "SZ300750",  # 宁德时代
        "SZ300059",  # 东方财富
    ]

    lab.load_data(
        codes=codes,
        start="2023-01-01",
        end="2024-12-31"
    )

    # ========== 2. 计算因子 ==========
    print("\n[步骤2] 计算因子")
    print("-" * 50)

    # 方式1: 从因子库添加
    lab.add_factor_from_library('momentum', [5, 10, 20])
    lab.add_factor_from_library('rsi', [6, 12, 24])
    lab.add_factor_from_library('ma', [5, 10, 20, 60])
    lab.add_factor_from_library('volatility', [10, 20])
    lab.add_factor_from_library('volume_ratio', [10, 20])
    lab.add_factor_from_library('ma_bias', [10, 20])

    print(f"已计算 {len(lab.factor_data)} 个因子: {list(lab.factor_data.keys())}")

    # 方式2: 自定义因子
    def custom_momentum(df, short=5, long=20):
        """自定义动量因子"""
        short_ma = df['close'].rolling(short).mean()
        long_ma = df['close'].rolling(long).mean()
        return (short_ma / long_ma - 1)

    lab.calculate_factor('custom_mom', custom_momentum, short=5, long=20)

    print(f"自定义因子: custom_mom")

    # ========== 3. 因子研究 ==========
    print("\n[步骤3] 因子研究")
    print("-" * 50)

    # 选择要研究的因子
    factor_cols = [
        'momentum_5', 'momentum_10', 'momentum_20',
        'rsi_6', 'rsi_12',
        'ma_5', 'ma_20', 'ma_60',
        'volatility_10', 'volatility_20',
        'volume_ratio_10', 'volume_ratio_20',
        'ma_bias_10', 'ma_bias_20',
        'custom_mom'
    ]

    lab.study_factors(factor_cols)

    # ========== 4. 策略回测 ==========
    print("\n[步骤4] 策略回测")
    print("-" * 50)

    # 均线策略
    strategy1 = MAStrategy(short_period=5, long_period=20)
    lab.backtest(strategy1, name="MA(5,20)")

    strategy2 = MAStrategy(short_period=10, long_period=30)
    lab.backtest(strategy2, name="MA(10,30)")

    # ========== 5. 参数优化 ==========
    print("\n[步骤5] 参数优化")
    print("-" * 50)

    param_grid = {
        "short_period": [3, 5, 7, 10],
        "long_period": [20, 30, 40],
    }

    optimize_results = lab.optimize(
        MAStrategy,
        param_grid,
        objective="sharpe_ratio",
        method="grid"
    )

    # ========== 6. 策略对比 ==========
    print("\n[步骤6] 策略对比")
    print("-" * 50)

    lab.compare_strategies()

    # ========== 7. 获取报告 ==========
    print("\n[步骤7] 研究报告")
    print("-" * 50)

    report = lab.get_report()

    print(f"\n研究配置:")
    print(f"  实验室名称: {report['config'].name}")
    print(f"  初始资金: {report['config'].initial_capital:,}")
    print(f"  基准: {report['config'].benchmark}")

    print(f"\n数据信息:")
    print(f"  记录数: {report['data_info']['n_records']}")
    print(f"  股票数: {report['data_info']['n_stocks']}")
    print(f"  时间范围: {report['data_info']['date_range']}")

    print(f"\n因子数量: {len(report['factor_results'])}")
    print(f"策略数量: {len(report['backtest_results'])}")

    # 保存报告
    # lab.save_report("quantlab_report.json")

    print("\n" + "="*70)
    print("工作流程完成!")
    print("="*70)


def example_factor_ic_only():
    """仅因子IC分析示例"""
    print("\n" + "="*70)
    print("示例: 因子IC分析")
    print("="*70)

    from finquant.research import QuantLab
    from finquant.data.factors import FactorLibrary

    lab = QuantLab()

    # 加载数据
    lab.load_data(
        codes=["SH600519", "SH600036", "SZ300750"],
        start="2023-01-01",
        end="2024-12-31"
    )

    # 添加因子
    lab.add_factor_from_library('momentum', [5, 10, 20])
    lab.add_factor_from_library('rsi', [6, 12, 24])

    # 因子研究
    lab.study_factors(['momentum_5', 'momentum_10', 'rsi_6', 'rsi_12'])


def example_backtest_only():
    """仅回测示例"""
    print("\n" + "="*70)
    print("示例: 策略回测")
    print("="*70)

    from finquant.research import QuantLab
    from finquant.strategy import MAStrategy, RSIStrategy

    lab = QuantLab()

    # 加载数据
    lab.load_data(
        codes=["SH600519"],
        start="2023-01-01",
        end="2024-12-31"
    )

    # 回测多个策略
    lab.backtest(MAStrategy(short_period=5, long_period=20), name="MA")
    lab.backtest(MAStrategy(short_period=10, long_period=30), name="MA2")
    lab.backtest(RSIStrategy(period=14, oversold=30, overbought=70), name="RSI")

    # 对比
    lab.compare_strategies()


def example_optimize_only():
    """仅参数优化示例"""
    print("\n" + "="*70)
    print("示例: 参数优化")
    print("="*70)

    from finquant.research import QuantLab
    from finquant.strategy import MAStrategy

    lab = QuantLab()

    # 加载数据
    lab.load_data(
        codes=["SH600519"],
        start="2023-01-01",
        end="2024-12-31"
    )

    # 参数优化
    param_grid = {
        "short_period": [3, 5, 7],
        "long_period": [20, 30, 40],
    }

    results = lab.optimize(
        MAStrategy,
        param_grid,
        objective="sharpe_ratio",
        method="grid"
    )

    print("\n优化结果:")
    print(results.to_string(index=False))


if __name__ == "__main__":
    # 选择要运行的示例

    # 示例1: 完整工作流程
    example_full_workflow()

    # 示例2: 仅因子IC分析
    # example_factor_ic_only()

    # 示例3: 仅回测
    # example_backtest_only()

    # 示例4: 仅参数优化
    # example_optimize_only()
