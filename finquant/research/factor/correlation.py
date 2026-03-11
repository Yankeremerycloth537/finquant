"""
finquant - 因子相关性分析模块

提供因子相关性分析功能：
- 皮尔逊相关系数
- Spearman秩相关系数
- 滚动相关性
- 相关性热图
- 因子正交化
"""

from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass
class CorrelationResult:
    """相关性分析结果"""
    factor_pairs: List[Tuple[str, str]]
    pearson_matrix: pd.DataFrame
    spearman_matrix: pd.DataFrame
    high_corr_pairs: List[Dict]  # 高相关性因子对


class FactorCorrelation:
    """
    因子相关性分析

    分析因子之间的相关性，帮助选择低相关性的因子组合
    """

    def __init__(self, threshold: float = 0.8):
        """
        Args:
            threshold: 高相关性阈值，默认0.8
        """
        self.threshold = threshold
        self.results: Optional[CorrelationResult] = None

    def calculate_correlation(
        self,
        data: pd.DataFrame,
        factor_cols: List[str],
        method: str = "pearson",
    ) -> pd.DataFrame:
        """
        计算因子相关性矩阵

        Args:
            data: 包含因子数据
            factor_cols: 因子列列表
            method: "pearson" 或 "spearman"

        Returns:
            相关性矩阵
        """
        # 提取因子数据
        factor_data = data[factor_cols].copy()

        # 去除NaN
        factor_data = factor_data.dropna()

        if factor_data.empty:
            return pd.DataFrame()

        # 计算相关性
        if method == "pearson":
            corr = factor_data.corr(method='pearson')
        elif method == "spearman":
            corr = factor_data.corr(method='spearman')
        else:
            raise ValueError(f"Unknown method: {method}")

        return corr

    def find_high_correlation_pairs(
        self,
        corr_matrix: pd.DataFrame,
        threshold: float = None,
    ) -> List[Dict]:
        """
        找出高相关性因子对

        Args:
            corr_matrix: 相关性矩阵
            threshold: 阈值，默认使用实例阈值

        Returns:
            高相关性因子对列表
        """
        if threshold is None:
            threshold = self.threshold

        high_corr = []

        # 获取上三角矩阵（避免重复）
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]

                if abs(corr_value) >= threshold:
                    high_corr.append({
                        'factor1': col1,
                        'factor2': col2,
                        'correlation': corr_value,
                    })

        # 按绝对值排序
        high_corr.sort(key=lambda x: abs(x['correlation']), reverse=True)

        return high_corr

    def analyze(
        self,
        data: pd.DataFrame,
        factor_cols: List[str],
    ) -> CorrelationResult:
        """
        完整相关性分析

        Args:
            data: 包含因子数据
            factor_cols: 因子列列表

        Returns:
            CorrelationResult
        """
        # 计算两种相关性
        pearson = self.calculate_correlation(data, factor_cols, 'pearson')
        spearman = self.calculate_correlation(data, factor_cols, 'spearman')

        # 找出高相关性因子对
        high_corr = self.find_high_correlation_pairs(pearson)

        # 存储结果
        self.results = CorrelationResult(
            factor_pairs=[(f1, f2) for f1, f2 in zip(factor_cols[:-1], factor_cols[1:])],
            pearson_matrix=pearson,
            spearman_matrix=spearman,
            high_corr_pairs=high_corr,
        )

        return self.results

    def get_summary(self) -> pd.DataFrame:
        """获取高相关性因子对汇总"""
        if self.results is None:
            return pd.DataFrame()

        if not self.results.high_corr_pairs:
            return pd.DataFrame(columns=['factor1', 'factor2', 'correlation'])

        return pd.DataFrame(self.results.high_corr_pairs)


class RollingCorrelation:
    """
    滚动相关性分析

    计算因子在滚动窗口期内的相关性变化
    """

    def __init__(self, window: int = 60):
        """
        Args:
            window: 滚动窗口大小
        """
        self.window = window

    def calculate(
        self,
        data: pd.DataFrame,
        factor1: str,
        factor2: str,
    ) -> pd.Series:
        """
        计算滚动相关性

        Args:
            data: 包含因子数据
            factor1: 因子1列名
            factor2: 因子2列名

        Returns:
            滚动相关性序列
        """
        rolling_corr = data[factor1].rolling(window=self.window).corr(data[factor2])
        return rolling_corr

    def analyze(
        self,
        data: pd.DataFrame,
        factor_cols: List[str],
    ) -> pd.DataFrame:
        """
        批量计算因子对的滚动相关性

        Args:
            data: 包含因子数据
            factor_cols: 因子列列表

        Returns:
            滚动相关性矩阵
        """
        results = []

        for i in range(len(factor_cols)):
            for j in range(i + 1, len(factor_cols)):
                f1 = factor_cols[i]
                f2 = factor_cols[j]

                rolling_corr = self.calculate(data, f1, f2)

                results.append({
                    'factor1': f1,
                    'factor2': f2,
                    'corr_mean': rolling_corr.mean(),
                    'corr_std': rolling_corr.std(),
                    'corr_min': rolling_corr.min(),
                    'corr_max': rolling_corr.max(),
                })

        return pd.DataFrame(results)


class FactorOrthogonalizer:
    """
    因子正交化

    将因子对主成分或参考因子进行正交化处理
    """

    @staticmethod
    def orthogonalize_to_reference(
        data: pd.DataFrame,
        factor_col: str,
        reference_col: str,
    ) -> pd.Series:
        """
        将因子对参考因子正交化

        Args:
            data: 数据
            factor_col: 待正交化的因子
            reference_col: 参考因子

        Returns:
            正交化后的因子
        """
        # 去除NaN
        valid_mask = ~(data[factor_col].isna() | data[reference_col].isna())

        if valid_mask.sum() < 10:
            return data[factor_col]

        # 线性回归
        x = data.loc[valid_mask, reference_col].values.reshape(-1, 1)
        y = data.loc[valid_mask, factor_col].values

        from numpy.linalg import lstsq
        coef, _, _, _ = lstsq(x, y, rcond=None)

        # 计算残差
        residual = data[factor_col] - coef[0] * data[reference_col]

        return residual

    @staticmethod
    def orthogonalize_to_factor_group(
        data: pd.DataFrame,
        target_col: str,
        reference_cols: List[str],
    ) -> pd.Series:
        """
        将因子对因子组正交化（去除因子组内的共有信息）

        Args:
            data: 数据
            target_col: 目标因子
            reference_cols: 参考因子列表

        Returns:
            正交化后的因子
        """
        # 去除NaN
        valid_mask = data[reference_cols + [target_col]].notna().all(axis=1)

        if valid_mask.sum() < 10:
            return data[target_col]

        X = data.loc[valid_mask, reference_cols].values
        y = data.loc[valid_mask, target_col].values

        # 多元线性回归
        from numpy.linalg import lstsq
        coef, _, _, _ = lstsq(X, y, rcond=None)

        # 计算预测值
        y_pred = X @ coef

        # 计算残差
        residual = data[target_col].copy()
        residual.loc[valid_mask] = y - y_pred

        return residual

    @staticmethod
    def pca_transform(
        data: pd.DataFrame,
        factor_cols: List[str],
        n_components: int = None,
    ) -> pd.DataFrame:
        """
        PCA变换

        Args:
            data: 数据
            factor_cols: 因子列列表
            n_components: 主成分数量，默认保留所有

        Returns:
            主成分数据
        """
        # 提取因子数据
        factor_data = data[factor_cols].copy()
        factor_data = factor_data.dropna()

        if factor_data.empty:
            return pd.DataFrame()

        # 标准化
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        standardized = scaler.fit_transform(factor_data)

        # PCA
        from sklearn.decomposition import PCA
        n_components = n_components or len(factor_cols)
        pca = PCA(n_components=min(n_components, standardized.shape[1]))
        components = pca.fit_transform(standardized)

        # 返回主成分
        result = pd.DataFrame(
            components,
            index=factor_data.index,
            columns=[f'PC{i+1}' for i in range(components.shape[1])]
        )

        return result


# ========== 便捷函数 ==========


def factor_correlation(
    data: pd.DataFrame,
    factor_cols: List[str],
    threshold: float = 0.8,
) -> CorrelationResult:
    """
    快速因子相关性分析

    Args:
        data: 数据
        factor_cols: 因子列列表
        threshold: 高相关性阈值

    Returns:
        相关性分析结果
    """
    analyzer = FactorCorrelation(threshold=threshold)
    return analyzer.analyze(data, factor_cols)


def orthogonalize_factor(
    data: pd.DataFrame,
    factor_col: str,
    reference_cols: Union[str, List[str]],
) -> pd.Series:
    """
    快速因子正交化

    Args:
        data: 数据
        factor_col: 待正交化的因子
        reference_cols: 参考因子

    Returns:
        正交化后的因子
    """
    if isinstance(reference_cols, str):
        reference_cols = [reference_cols]

    if len(reference_cols) == 1:
        return FactorOrthogonalizer.orthogonalize_to_reference(
            data, factor_col, reference_cols[0]
        )
    else:
        return FactorOrthogonalizer.orthogonalize_to_factor_group(
            data, factor_col, reference_cols
        )


__all__ = [
    "CorrelationResult",
    "FactorCorrelation",
    "RollingCorrelation",
    "FactorOrthogonalizer",
    "factor_correlation",
    "orthogonalize_factor",
]
