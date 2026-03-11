"""
finquant - 因子分组回测模块

提供单因子分层回测功能：
- 按因子值将股票分组
- 计算每组收益和风险指标
- 多空组合分析
- 分组轮动策略回测
"""

from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import numpy as np


@dataclass
class GroupResult:
    """分组回测结果"""
    group: int
    n_stocks: int              # 股票数量
    total_return: float        # 总收益率
    annual_return: float       # 年化收益率
    volatility: float         # 年化波动率
    sharpe_ratio: float        # 夏普比率
    max_drawdown: float       # 最大回撤
    win_rate: float            # 胜率
    avg_return: float          # 平均收益
    std_return: float          # 收益标准差


@dataclass
class BacktestResult:
    """分组回测结果汇总"""
    factor_name: str
    n_groups: int
    results: List[GroupResult] = field(default_factory=list)

    # 多空组合
    long_short_return: float = 0
    long_short_sharpe: float = 0

    # 时间范围
    start_date: str = ""
    end_date: str = ""

    # 每日收益
    daily_returns: pd.DataFrame = None


class FactorBacktest:
    """
    因子分组回测

    将股票按因子值分成n组，回测每组的收益表现
    """

    def __init__(
        self,
        n_groups: int = 5,
        rebalance_days: int = 5,
        initial_capital: float = 1000000,
        commission_rate: float = 0.0003,
    ):
        """
        Args:
            n_groups: 分组数量
            rebalance_days: 调仓周期(天)
            initial_capital: 初始资金
            commission_rate: 手续费率
        """
        self.n_groups = n_groups
        self.rebalance_days = rebalance_days
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate

    def assign_groups(
        self,
        data: pd.DataFrame,
        factor_col: str,
    ) -> pd.DataFrame:
        """
        根据因子值分配分组

        Args:
            data: 包含因子值的数据
            factor_col: 因子列名

        Returns:
            添加了group列的数据
        """
        df = data.copy()

        # 按日期分组分配
        df['group'] = df.groupby('trade_date')[factor_col].transform(
            lambda x: pd.qcut(x, q=self.n_groups, labels=False, duplicates='drop')
        )

        return df

    def calculate_portfolio_returns(
        self,
        data: pd.DataFrame,
        group: int,
    ) -> pd.Series:
        """
        计算组合收益

        Args:
            data: 包含分组和收益的数据
            group: 组号 (0为最低因子值, n_groups-1为最高)

        Returns:
            每日收益序列
        """
        group_data = data[data['group'] == group]

        # 按日期计算等权收益
        daily = group_data.groupby('trade_date')['forward_return'].mean()

        return daily

    def run(
        self,
        data: pd.DataFrame,
        factor_col: str,
        forward_return_col: str = "forward_return",
    ) -> BacktestResult:
        """
        执行因子分组回测

        Args:
            data: 包含因子和收益的数据
            factor_col: 因子列名
            forward_return_col: 未来收益列名

        Returns:
            BacktestResult: 回测结果
        """
        # 分配分组
        df = self.assign_groups(data, factor_col)

        # 获取日期范围
        dates = sorted(df['trade_date'].unique())

        results = []
        group_returns = {}

        # 计算每组收益
        for group in range(self.n_groups):
            daily_returns = self.calculate_portfolio_returns(df, group)
            group_returns[group] = daily_returns

            # 计算统计指标
            if daily_returns.empty:
                continue

            # 总收益
            total_return = (1 + daily_returns).prod() - 1

            # 年化收益 (假设252交易日)
            n_days = len(daily_returns)
            years = n_days / 252
            annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

            # 波动率
            volatility = daily_returns.std() * np.sqrt(252)

            # 夏普比率
            sharpe = annual_return / volatility if volatility > 0 else 0

            # 最大回撤
            cumulative = (1 + daily_returns).cumprod()
            peak = cumulative.cummax()
            drawdown = (cumulative - peak) / peak
            max_dd = drawdown.min()

            # 胜率
            win_rate = (daily_returns > 0).mean()

            # 平均收益和标准差
            avg_return = daily_returns.mean()
            std_return = daily_returns.std()

            # 股票数量
            n_stocks = df[df['group'] == group]['code'].nunique()

            results.append(GroupResult(
                group=group,
                n_stocks=n_stocks,
                total_return=total_return,
                annual_return=annual_return,
                volatility=volatility,
                sharpe_ratio=sharpe,
                max_drawdown=max_dd,
                win_rate=win_rate,
                avg_return=avg_return,
                std_return=std_return,
            ))

        # 计算多空组合
        long_short = None
        if 0 in group_returns and self.n_groups - 1 in group_returns:
            # 多头: 最高因子组
            long = group_returns[self.n_groups - 1]
            # 空头: 最低因子组
            short = group_returns[0]

            # 对齐日期
            common_dates = long.index.intersection(short.index)
            long = long.loc[common_dates]
            short = short.loc[common_dates]

            # 多空收益
            long_short = long - short

        result = BacktestResult(
            factor_name=factor_col,
            n_groups=self.n_groups,
            results=results,
        )

        if long_short is not None and not long_short.empty:
            ls_total = (1 + long_short).prod() - 1
            ls_annual = (1 + ls_total) ** (252 / len(long_short)) - 1
            ls_vol = long_short.std() * np.sqrt(252)
            result.long_short_return = ls_total
            result.long_short_sharpe = ls_annual / ls_vol if ls_vol > 0 else 0

            # 保存多空每日收益
            result.daily_returns = pd.DataFrame({
                'long': long,
                'short': short,
                'long_short': long_short,
            })

        if dates:
            result.start_date = str(dates[0])[:10]
            result.end_date = str(dates[-1])[:10]

        return result

    def get_summary(self, result: BacktestResult) -> pd.DataFrame:
        """获取汇总表格"""
        rows = []
        for r in result.results:
            rows.append({
                'group': r.group,
                'n_stocks': r.n_stocks,
                'total_return': r.total_return,
                'annual_return': r.annual_return,
                'volatility': r.volatility,
                'sharpe': r.sharpe_ratio,
                'max_drawdown': r.max_drawdown,
                'win_rate': r.win_rate,
            })

        df = pd.DataFrame(rows)

        # 添加多空组合
        if result.long_short_return != 0:
            df = pd.concat([df, pd.DataFrame([{
                'group': 'LS',
                'n_stocks': '-',
                'total_return': result.long_short_return,
                'annual_return': '-',
                'volatility': '-',
                'sharpe': result.long_short_sharpe,
                'max_drawdown': '-',
                'win_rate': '-',
            }])], ignore_index=True)

        return df


class RollingGroupBacktest:
    """
    滚动分组回测

    定期重新分组，计算分组的动态表现
    """

    def __init__(
        self,
        n_groups: int = 5,
        rebalance_days: int = 20,
    ):
        """
        Args:
            n_groups: 分组数量
            rebalance_days: 调仓周期
        """
        self.n_groups = n_groups
        self.rebalance_days = rebalance_days

    def run(
        self,
        data: pd.DataFrame,
        factor_col: str,
        forward_return_col: str = "forward_return",
    ) -> pd.DataFrame:
        """
        执行滚动分组回测

        Args:
            data: 包含因子和收益的数据
            factor_col: 因子列名
            forward_return_col: 未来收益列名

        Returns:
            滚动回测结果
        """
        dates = sorted(data['trade_date'].unique())
        results = []

        for i in range(0, len(dates) - self.rebalance_days, self.rebalance_days):
            # 当前调仓日
            rebalance_date = dates[i]

            # 获取调仓窗口期数据
            window_data = data[
                (data['trade_date'] >= rebalance_date) &
                (data['trade_date'] < dates[min(i + self.rebalance_days, len(dates) - 1)])
            ]

            if window_data.empty:
                continue

            # 分配分组
            window_data = window_data.copy()
            window_data['group'] = window_data.groupby('trade_date')[factor_col].transform(
                lambda x: pd.qcut(x, q=self.n_groups, labels=False, duplicates='drop')
            )

            # 计算每组收益
            for group in range(self.n_groups):
                group_data = window_data[window_data['group'] == group]
                if group_data.empty:
                    continue

                ret = group_data.groupby('trade_date')[forward_return_col].mean()

                results.append({
                    'rebalance_date': rebalance_date,
                    'group': group,
                    'return': ret.mean(),
                    'n_days': len(ret),
                })

        return pd.DataFrame(results)


# ========== 便捷函数 ==========


def factor_backtest(
    data: pd.DataFrame,
    factor_col: str,
    forward_return_col: str = "forward_return",
    n_groups: int = 5,
    rebalance_days: int = 5,
) -> BacktestResult:
    """
    快速因子分组回测

    Args:
        data: 数据
        factor_col: 因子列
        forward_return_col: 未来收益列
        n_groups: 分组数
        rebalance_days: 调仓周期

    Returns:
        回测结果
    """
    bt = FactorBacktest(n_groups=n_groups, rebalance_days=rebalance_days)
    return bt.run(data, factor_col, forward_return_col)


__all__ = [
    "GroupResult",
    "BacktestResult",
    "FactorBacktest",
    "RollingGroupBacktest",
    "factor_backtest",
]
