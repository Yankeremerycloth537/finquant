"""
finquant - 因子研究示例

演示如何使用因子研究功能：
- IC分析
- 分组回测
"""

import pandas as pd
import numpy as np


def prepare_factor_data(codes, start="2023-01-01", end="2024-12-31"):
    """准备因子数据"""
    from finquant import get_kline
    from finquant.data.factors import FactorLibrary

    # 获取数据
    data = get_kline(codes, start=start, end=end)
    print(f"获取数据: {len(data)} 条")

    # 按股票分组计算因子
    factor_data = []
    for code in codes:
        code_data = data[data['code'] == code].copy()
        code_data = code_data.sort_values('trade_date')

        # 计算各种因子
        code_data['momentum_5'] = FactorLibrary.momentum(code_data['close'], 5)
        code_data['momentum_10'] = FactorLibrary.momentum(code_data['close'], 10)
        code_data['momentum_20'] = FactorLibrary.momentum(code_data['close'], 20)
        code_data['rsi_14'] = FactorLibrary.rsi(code_data['close'], 14)
        code_data['ma_bias_20'] = FactorLibrary.ma_bias(code_data['close'], 20)
        code_data['volatility_20'] = FactorLibrary.volatility(code_data['close'], 20)
        code_data['volume_ratio_20'] = FactorLibrary.volume_ratio(code_data['volume'], 20)

        # 计算未来收益 (5天后收益)
        code_data['forward_return'] = code_data['close'].shift(-5) / code_data['close'] - 1

        factor_data.append(code_data)

    # 合并所有股票数据
    df = pd.concat(factor_data, ignore_index=True)
    print(f"因子数据: {len(df)} 条")

    return df


# ========== 示例1：因子IC分析 ==========

def example_ic_analysis():
    """因子IC分析示例"""
    print("\n" + "="*60)
    print("示例1：因子IC分析")
    print("="*60)

    from finquant.research import FactorICAnalyzer

    # 多只股票
    codes = [
        "SH600519",  # 茅台
        "SH600036",  # 招商银行
        "SZ300750",  # 宁德时代
        "SZ300059",  # 东方财富
    ]

    df = prepare_factor_data(codes)

    # 因子IC分析
    factor_cols = [
        'momentum_5', 'momentum_10', 'momentum_20',
        'rsi_14', 'ma_bias_20', 'volatility_20', 'volume_ratio_20'
    ]

    analyzer = FactorICAnalyzer()
    results = analyzer.analyze(df, factor_cols, forward_return_col='forward_return')

    print("\n因子IC分析结果:")
    print("-" * 80)
    print(f"{'因子':<20} {'IC均值':>10} {'IC标准差':>10} {'IC_IR':>10} {'正相关比例':>12}")
    print("-" * 80)

    for _, row in results.iterrows():
        print(f"{row['factor']:<20} {row['ic_mean']:>10.4f} {row['ic_std']:>10.4f} "
              f"{row['ic_ir']:>10.4f} {row['ic_positive_rate']:>12.2%}")

    # 获取汇总信息
    summary = analyzer.get_summary()
    print("\n因子评级汇总:")
    print(summary[['factor', 'ic_mean', 'ic_ir', 'ic_rating', 'ir_rating']].to_string(index=False))


# ========== 示例2：因子分组回测 ==========

def example_factor_backtest():
    """因子分组回测示例"""
    print("\n" + "="*60)
    print("示例2：因子分组回测")
    print("="*60)

    from finquant.research import FactorBacktest

    # 多只股票
    codes = [
        "SH600519",  # 茅台
        "SH600036",  # 招商银行
        "SZ300750",  # 宁德时代
        "SZ300059",  # 东方财富
    ]

    df = prepare_factor_data(codes)

    # 因子分组回测
    factor_cols = ['momentum_10', 'rsi_14', 'ma_bias_20']

    bt = FactorBacktest(n_groups=5)

    for factor_col in factor_cols:
        print(f"\n{'='*40}")
        print(f"因子: {factor_col}")
        print(f"{'='*40}")

        # 去除NaN
        valid_df = df.dropna(subset=[factor_col, 'forward_return'])

        # 运行回测
        result = bt.run(valid_df, factor_col, forward_return_col='forward_return')

        # 打印结果
        summary = bt.get_summary(result)
        print(f"\n{summary.to_string(index=False)}")

        print(f"\n多空组合:")
        print(f"  多空收益: {result.long_short_return:.2%}")
        print(f"  多空夏普: {result.long_short_sharpe:.4f}")


# ========== 示例3：分组IC分析 ==========

def example_group_ic():
    """分组IC分析示例"""
    print("\n" + "="*60)
    print("示例3：分组IC分析")
    print("="*60)

    from finquant.research import GroupICAnalyzer

    # 获取数据
    data = get_kline(["SH600519"], start="2023-01-01", end="2024-12-31")
    data = data.sort_values('trade_date')

    # 计算因子
    data['momentum_10'] = FactorLibrary.momentum(data['close'], 10)
    data['rsi_14'] = FactorLibrary.rsi(data['close'], 14)
    data['forward_return'] = data['close'].shift(-5) / data['close'] - 1

    # 去除NaN
    data = data.dropna()

    # 分组IC分析
    analyzer = GroupICAnalyzer(n_groups=5)

    print("\n动量因子分组分析:")
    group_results = analyzer.analyze(data, 'momentum_10', 'forward_return')
    print(group_results.to_string(index=False))

    # 计算多空收益
    ls_return = analyzer.calculate_long_short_return(data, 'momentum_10', 'forward_return')
    print(f"\n多空组合收益:")
    print(f"  多头收益: {ls_return['long_return']:.4%}")
    print(f"  空头收益: {ls_return['short_return']:.4%}")
    print(f"  多空收益: {ls_return['long_short_return']:.4%}")


# ========== 示例4：快速IC计算 ==========

def example_quick_ic():
    """快速IC计算示例"""
    print("\n" + "="*60)
    print("示例4：快速IC计算")
    print("="*60)

    from finquant import get_kline
    from finquant.research import calc_ic, calc_rank_ic
    from finquant.data.factors import FactorLibrary

    # 获取数据
    data = get_kline(["SH600519"], start="2023-01-01", end="2024-12-31")
    data = data.sort_values('trade_date')

    # 计算因子和未来收益
    data['momentum_20'] = FactorLibrary.momentum(data['close'], 20)
    data['forward_return'] = data['close'].shift(-5) / data['close'] - 1

    # 快速计算IC
    ic = calc_ic(data, 'momentum_20', 'forward_return')
    rank_ic = calc_rank_ic(data, 'momentum_20', 'forward_return')

    print(f"\n动量因子(20日):")
    print(f"  IC: {ic:.4f}")
    print(f"  RankIC: {rank_ic:.4f}")


if __name__ == "__main__":
    # 示例1: 因子IC分析
    # example_ic_analysis()

    # 示例2: 因子分组回测
    # example_factor_backtest()

    # 示例3: 分组IC分析
    # example_group_ic()

    # 示例4: 快速IC计算
    # example_quick_ic()

    print("请取消注释要运行的示例")
