"""
finquant - 因子IC分析模块

提供因子预测能力评估：
- IC (Information Coefficient) 分析
- IR (Information Ratio) 分析
- 分组IC统计
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
import pandas as pd
import numpy as np


@dataclass
class ICResult:
    """IC分析结果"""
    factor_name: str
    ic_series: pd.Series           # 每日IC
    ic_mean: float                # IC均值
    ic_std: float                 # IC标准差
    ic_ir: float                  # IC_IR (IC均值/IC标准差)
    ic_positive_rate: float       # IC正相关比例
    ic_cumsum: pd.Series          # 累计IC
    rank_ic_mean: float           # RankIC均值
    rank_ic_ir: float             # RankIC_IR


class FactorICAnalyzer:
    """
    因子IC分析

    IC (Information Coefficient) = 因子值与未来收益的相关系数
    RankIC = 因子值与未来收益的秩相关系数

    判断标准：
    - IC均值 > 0.02: 因子有预测能力
    - IC_IR > 0.5: 因子稳定有效
    - IC正相关比例 > 0.55: 方向一致
    """

    def __init__(self, n_groups: int = 5):
        """
        Args:
            n_groups: 分组数量（用于分组IC计算）
        """
        self.n_groups = n_groups
        self.results: Dict[str, ICResult] = {}

    def calculate_ic(
        self,
        factor_values: pd.Series,
        forward_returns: pd.Series,
    ) -> float:
        """
        计算单期IC（皮尔逊相关系数）

        Args:
            factor_values: 因子值
            forward_returns: 未来收益

        Returns:
            IC值
        """
        # 去除NaN
        valid_mask = ~(factor_values.isna() | forward_returns.isna())
        if valid_mask.sum() < 10:
            return np.nan

        return factor_values[valid_mask].corr(forward_returns[valid_mask])

    def calculate_rank_ic(
        self,
        factor_values: pd.Series,
        forward_returns: pd.Series,
    ) -> float:
        """
        计算单期RankIC（Spearman秩相关系数）

        Args:
            factor_values: 因子值
            forward_returns: 未来收益

        Returns:
            RankIC值
        """
        # 去除NaN
        valid_mask = ~(factor_values.isna() | forward_returns.isna())
        if valid_mask.sum() < 10:
            return np.nan

        return factor_values[valid_mask].corr(forward_returns[valid_mask], method='spearman')

    def calculate_daily_ic(
        self,
        data: pd.DataFrame,
        factor_col: str,
        forward_return_col: str = "forward_return",
    ) -> pd.DataFrame:
        """
        计算每日IC

        Args:
            data: 包含因子和收益的数据
            factor_col: 因子列名
            forward_return_col: 未来收益列名

        Returns:
            每日IC的DataFrame
        """
        if 'trade_date' not in data.columns:
            raise ValueError("data must contain 'trade_date' column")

        daily_ic = []

        for date, group in data.groupby('trade_date'):
            ic = self.calculate_ic(
                group[factor_col],
                group[forward_return_col]
            )
            rank_ic = self.calculate_rank_ic(
                group[factor_col],
                group[forward_return_col]
            )

            daily_ic.append({
                'trade_date': date,
                'ic': ic,
                'rank_ic': rank_ic,
            })

        return pd.DataFrame(daily_ic)

    def analyze(
        self,
        data: pd.DataFrame,
        factor_cols: Union[str, List[str]],
        forward_return_col: str = "forward_return",
    ) -> pd.DataFrame:
        """
        批量因子IC分析

        Args:
            data: 包含因子和收益的数据，必须包含 trade_date 列
            factor_cols: 因子列名或列名列表
            forward_return_col: 未来收益列名

        Returns:
            IC分析结果DataFrame
        """
        if isinstance(factor_cols, str):
            factor_cols = [factor_cols]

        results = []

        for factor_col in factor_cols:
            # 计算每日IC
            daily_ic = self.calculate_daily_ic(
                data, factor_col, forward_return_col
            )

            if daily_ic.empty or daily_ic['ic'].isna().all():
                # 如果每日IC计算失败，尝试使用整体IC
                valid_data = data.dropna(subset=[factor_col, forward_return_col])
                if len(valid_data) > 10:
                    ic_mean = self.calculate_ic(
                        valid_data[factor_col],
                        valid_data[forward_return_col]
                    )
                    ic_std = 0
                    ic_ir = 0
                    rank_ic_mean = self.calculate_rank_ic(
                        valid_data[factor_col],
                        valid_data[forward_return_col]
                    )
                    rank_ic_ir = 0
                    ic_positive_rate = 1.0 if ic_mean > 0 else 0.0
                    n_days = len(valid_data)

                    self.results[factor_col] = ICResult(
                        factor_name=factor_col,
                        ic_series=pd.Series([ic_mean]),
                        ic_mean=ic_mean,
                        ic_std=ic_std,
                        ic_ir=ic_ir,
                        ic_positive_rate=ic_positive_rate,
                        ic_cumsum=pd.Series([ic_mean]),
                        rank_ic_mean=rank_ic_mean,
                        rank_ic_ir=rank_ic_ir,
                    )

                    results.append({
                        'factor': factor_col,
                        'ic_mean': ic_mean,
                        'ic_std': ic_std,
                        'ic_ir': ic_ir,
                        'ic_positive_rate': ic_positive_rate,
                        'rank_ic_mean': rank_ic_mean,
                        'rank_ic_ir': rank_ic_ir,
                        'n_days': n_days,
                    })
                continue

            # 计算统计指标
            ic_mean = daily_ic['ic'].mean()
            ic_std = daily_ic['ic'].std()
            ic_ir = ic_mean / ic_std if ic_std > 0 else 0

            rank_ic_mean = daily_ic['rank_ic'].mean()
            rank_ic_std = daily_ic['rank_ic'].std()
            rank_ic_ir = rank_ic_mean / rank_ic_std if rank_ic_std > 0 else 0

            # IC正相关比例
            ic_positive_rate = (daily_ic['ic'] > 0).mean()

            # 累计IC
            ic_cumsum = daily_ic['ic'].cumsum()

            # 存储结果
            self.results[factor_col] = ICResult(
                factor_name=factor_col,
                ic_series=daily_ic['ic'],
                ic_mean=ic_mean,
                ic_std=ic_std,
                ic_ir=ic_ir,
                ic_positive_rate=ic_positive_rate,
                ic_cumsum=ic_cumsum,
                rank_ic_mean=rank_ic_mean,
                rank_ic_ir=rank_ic_ir,
            )

            results.append({
                'factor': factor_col,
                'ic_mean': ic_mean,
                'ic_std': ic_std,
                'ic_ir': ic_ir,
                'ic_positive_rate': ic_positive_rate,
                'rank_ic_mean': rank_ic_mean,
                'rank_ic_ir': rank_ic_ir,
                'n_days': daily_ic['ic'].notna().sum(),
            })

        return pd.DataFrame(results)

    def get_result(self, factor_name: str) -> Optional[ICResult]:
        """获取单个因子的IC分析结果"""
        return self.results.get(factor_name)

    def get_summary(self) -> pd.DataFrame:
        """获取所有因子的IC汇总"""
        if not self.results:
            return pd.DataFrame()

        summary = []
        for name, result in self.results.items():
            summary.append({
                'factor': name,
                'ic_mean': result.ic_mean,
                'ic_std': result.ic_std,
                'ic_ir': result.ic_ir,
                'ic_positive_rate': result.ic_positive_rate,
                'rank_ic_mean': result.rank_ic_mean,
                'rank_ic_ir': result.rank_ic_ir,
            })

        df = pd.DataFrame(summary)

        # 添加评级
        def rate_ic(ic):
            if ic > 0.03:
                return 'A+'
            elif ic > 0.02:
                return 'A'
            elif ic > 0.01:
                return 'B'
            elif ic > 0:
                return 'C'
            else:
                return 'D'

        def rate_ir(ir):
            if ir > 0.8:
                return 'A+'
            elif ir > 0.5:
                return 'A'
            elif ir > 0.3:
                return 'B'
            elif ir > 0:
                return 'C'
            else:
                return 'D'

        df['ic_rating'] = df['ic_mean'].apply(rate_ic)
        df['ir_rating'] = df['ic_ir'].apply(rate_ir)

        # 按IC_IR排序
        df = df.sort_values('ic_ir', ascending=False)

        return df


class GroupICAnalyzer:
    """
    分组IC分析

    将股票按因子值分成n组，计算每组的平均收益
    """

    def __init__(self, n_groups: int = 5):
        """
        Args:
            n_groups: 分组数量
        """
        self.n_groups = n_groups

    def analyze(
        self,
        data: pd.DataFrame,
        factor_col: str,
        forward_return_col: str = "forward_return",
    ) -> pd.DataFrame:
        """
        执行分组IC分析

        Args:
            data: 包含因子和收益的数据
            factor_col: 因子列名
            forward_return_col: 未来收益列名

        Returns:
            分组结果
        """
        # 去除NaN
        valid_data = data.dropna(subset=[factor_col, forward_return_col])

        if valid_data.empty:
            return pd.DataFrame()

        # 按因子值分组
        try:
            valid_data = valid_data.copy()
            valid_data['group'] = pd.qcut(
                valid_data[factor_col],
                q=self.n_groups,
                labels=False,
                duplicates='drop'
            )
        except ValueError:
            # 如果分位数不唯一，使用rank分组
            valid_data = valid_data.copy()
            valid_data['rank'] = valid_data[factor_col].rank(pct=True)
            valid_data['group'] = (valid_data['rank'] * self.n_groups).astype(int)
            valid_data['group'] = valid_data['group'].clip(0, self.n_groups - 1)

        # 计算每组收益
        results = []
        for group in range(self.n_groups):
            group_data = valid_data[valid_data['group'] == group]

            if group_data.empty:
                continue

            results.append({
                'group': group,
                'return': group_data[forward_return_col].mean(),
                'std': group_data[forward_return_col].std(),
                'count': len(group_data),
                'factor_mean': group_data[factor_col].mean(),
            })

        return pd.DataFrame(results)

    def calculate_long_short_return(
        self,
        data: pd.DataFrame,
        factor_col: str,
        forward_return_col: str = "forward_return",
    ) -> Dict[str, float]:
        """
        计算多空组合收益

        Args:
            data: 包含因子和收益的数据
            factor_col: 因子列名
            forward_return_col: 未来收益列名

        Returns:
            多空收益统计
        """
        group_results = self.analyze(data, factor_col, forward_return_col)

        if group_results.empty:
            return {}

        # 多头组 (最高因子值)
        long_return = group_results[group_results['group'] == self.n_groups - 1]['return'].values[0]

        # 空头组 (最低因子值)
        short_return = group_results[group_results['group'] == 0]['return'].values[0]

        # 多空收益
        long_short = long_return - short_return

        return {
            'long_return': long_return,
            'short_return': short_return,
            'long_short_return': long_short,
            'group_return_spread': long_short,  # 别名
        }


# ========== 便捷函数 ==========


def calc_ic(
    data: pd.DataFrame,
    factor_col: str,
    forward_return_col: str = "forward_return",
) -> float:
    """
    快速计算IC

    Args:
        data: 数据
        factor_col: 因子列
        forward_return_col: 未来收益列

    Returns:
        IC值
    """
    analyzer = FactorICAnalyzer()
    return analyzer.calculate_ic(
        data[factor_col],
        data[forward_return_col]
    )


def calc_rank_ic(
    data: pd.DataFrame,
    factor_col: str,
    forward_return_col: str = "forward_return",
) -> float:
    """
    快速计算RankIC

    Args:
        data: 数据
        factor_col: 因子列
        forward_return_col: 未来收益列

    Returns:
        RankIC值
    """
    analyzer = FactorICAnalyzer()
    return analyzer.calculate_rank_ic(
        data[factor_col],
        data[forward_return_col]
    )


def analyze_factors(
    data: pd.DataFrame,
    factor_cols: List[str],
    forward_return_col: str = "forward_return",
) -> pd.DataFrame:
    """
    批量因子IC分析便捷函数

    Args:
        data: 数据
        factor_cols: 因子列列表
        forward_return_col: 未来收益列

    Returns:
        IC分析结果
    """
    analyzer = FactorICAnalyzer()
    return analyzer.analyze(data, factor_cols, forward_return_col)


__all__ = [
    "ICResult",
    "FactorICAnalyzer",
    "GroupICAnalyzer",
    "calc_ic",
    "calc_rank_ic",
    "analyze_factors",
]
