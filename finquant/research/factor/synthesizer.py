"""
finquant - 因子合成模块

提供多种因子合成方法：
- 等权合成
- IC加权合成
- PCA合成
- 因子组合优化
"""

from typing import Dict, List, Optional, Union, Callable
from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass
class SynthesisResult:
    """因子合成结果"""
    method: str                    # 合成方法
    weights: Dict[str, float]     # 因子权重
    ic_before: float              # 合成前IC
    ic_after: float               # 合成后IC
    factor_values: pd.Series      # 合成后的因子值


class FactorSynthesizer:
    """
    因子合成器

    将多个因子合成为单一复合因子
    """

    def __init__(self):
        pass

    def equal_weight(
        self,
        data: pd.DataFrame,
        factor_cols: List[str],
        name: str = "equal_weight",
    ) -> SynthesisResult:
        """
        等权合成

        Args:
            data: 包含因子数据
            factor_cols: 因子列列表
            name: 合成因子名称

        Returns:
            SynthesisResult
        """
        # 提取因子
        factor_data = data[factor_cols].copy()

        # 标准化（去量纲）
        factor_data = (factor_data - factor_data.mean()) / factor_data.std()

        # 等权平均
        synthetic = factor_data.mean(axis=1)

        # 权重
        weights = {col: 1.0 / len(factor_cols) for col in factor_cols}

        return SynthesisResult(
            method="equal_weight",
            weights=weights,
            ic_before=0,
            ic_after=0,
            factor_values=synthetic,
        )

    def ic_weight(
        self,
        data: pd.DataFrame,
        factor_cols: List[str],
        forward_return_col: str = "forward_return",
        name: str = "ic_weight",
    ) -> SynthesisResult:
        """
        IC加权合成

        根据因子的IC_IR进行加权，IC越高的因子权重越大

        Args:
            data: 包含因子和收益数据
            factor_cols: 因子列列表
            forward_return_col: 未来收益列
            name: 合成因子名称

        Returns:
            SynthesisResult
        """
        from finquant.research.factor.ic_analysis import FactorICAnalyzer

        # 计算每个因子的IC
        analyzer = FactorICAnalyzer()
        ic_results = analyzer.analyze(data, factor_cols, forward_return_col)

        # 获取IC_IR作为权重
        weights = {}
        for _, row in ic_results.iterrows():
            factor = row['factor']
            ic_ir = row['ic_ir']
            # 使用IC_IR作为权重（确保非负）
            weights[factor] = max(0, ic_ir)

        # 归一化权重
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        else:
            # 如果都为0，使用等权
            weights = {col: 1.0 / len(factor_cols) for col in factor_cols}

        # 计算合成因子
        factor_data = data[factor_cols].copy()
        factor_data = (factor_data - factor_data.mean()) / factor_data.std()

        synthetic = pd.Series(0, index=factor_data.index)
        for col, weight in weights.items():
            synthetic += factor_data[col] * weight

        # 计算IC（简化）
        ic_before = ic_results['ic_mean'].mean() if not ic_results.empty else 0

        return SynthesisResult(
            method="ic_weight",
            weights=weights,
            ic_before=ic_before,
            ic_after=0,
            factor_values=synthetic,
        )

    def ic_ir_weight(
        self,
        data: pd.DataFrame,
        factor_cols: List[str],
        forward_return_col: str = "forward_return",
        name: str = "ic_ir_weight",
    ) -> SynthesisResult:
        """
        IC_IR加权合成

        使用IC_IR（IC均值/IC标准差）作为权重，反映因子的稳定性和预测能力

        Args:
            data: 包含因子和收益数据
            factor_cols: 因子列列表
            forward_return_col: 未来收益列
            name: 合成因子名称

        Returns:
            SynthesisResult
        """
        from finquant.research.factor.ic_analysis import FactorICAnalyzer

        # 计算每个因子的IC
        analyzer = FactorICAnalyzer()
        ic_results = analyzer.analyze(data, factor_cols, forward_return_col)

        # 获取IC_IR作为权重
        weights = {}
        for _, row in ic_results.iterrows():
            factor = row['factor']
            ic_ir = row['ic_ir']
            # 使用IC_IR作为权重（确保非负）
            weights[factor] = max(0, ic_ir)

        # 归一化权重
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        else:
            weights = {col: 1.0 / len(factor_cols) for col in factor_cols}

        # 计算合成因子
        factor_data = data[factor_cols].copy()
        factor_data = (factor_data - factor_data.mean()) / factor_data.std()

        synthetic = pd.Series(0, index=factor_data.index)
        for col, weight in weights.items():
            synthetic += factor_data[col] * weight

        # 获取合成后的IC（简化估算）
        ic_before = ic_results['ic_ir'].mean() if not ic_results.empty else 0

        return SynthesisResult(
            method="ic_ir_weight",
            weights=weights,
            ic_before=ic_before,
            ic_after=0,
            factor_values=synthetic,
        )

    def pca_weight(
        self,
        data: pd.DataFrame,
        factor_cols: List[str],
        n_components: int = 1,
        name: str = "pca_weight",
    ) -> SynthesisResult:
        """
        PCA合成

        使用主成分分析提取主要信息

        Args:
            data: 包含因子数据
            factor_cols: 因子列列表
            n_components: 主成分数量
            name: 合成因子名称

        Returns:
            SynthesisResult
        """
        # 提取因子
        factor_data = data[factor_cols].copy()

        # 去除NaN
        factor_data = factor_data.dropna()

        if factor_data.empty:
            return SynthesisResult(
                method="pca_weight",
                weights={},
                ic_before=0,
                ic_after=0,
                factor_values=pd.Series(),
            )

        # 标准化
        factor_data = (factor_data - factor_data.mean()) / factor_data.std()

        # PCA
        from sklearn.decomposition import PCA
        pca = PCA(n_components=min(n_components, len(factor_cols)))
        components = pca.fit_transform(factor_data)

        # 第一主成分作为合成因子
        synthetic = pd.Series(components[:, 0], index=factor_data.index)

        # 计算权重（PCA载荷）
        loadings = pd.DataFrame(
            pca.components_.T,
            index=factor_cols,
            columns=[f'PC{i+1}' for i in range(len(pca.components_))]
        )

        weights = loadings['PC1'].to_dict()

        return SynthesisResult(
            method="pca_weight",
            weights=weights,
            ic_before=0,
            ic_after=0,
            factor_values=synthetic,
        )

    def optimize_weight(
        self,
        data: pd.DataFrame,
        factor_cols: List[str],
        forward_return_col: str = "forward_return",
        method: str = "max_ic",
        constraints: Dict = None,
    ) -> SynthesisResult:
        """
        优化权重合成

        使用优化方法寻找最优因子权重

        Args:
            data: 包含因子和收益数据
            factor_cols: 因子列列表
            forward_return_col: 未来收益列
            method: 优化目标 "max_ic" / "max_sharpe" / "min_volatility"
            constraints: 约束条件

        Returns:
            SynthesisResult
        """
        from scipy.optimize import minimize

        # 准备数据
        factor_data = data[factor_cols].copy()
        returns = data[forward_return_col]

        # 去除NaN
        valid_idx = factor_data.notna().all(axis=1) & returns.notna()
        factor_data = factor_data[valid_idx]
        returns = returns[valid_idx]

        if factor_data.empty:
            return SynthesisResult(
                method="optimize",
                weights={},
                ic_before=0,
                ic_after=0,
                factor_values=pd.Series(),
            )

        # 标准化
        factor_data = (factor_data - factor_data.mean()) / factor_data.std()

        n = len(factor_cols)

        def objective(weights):
            """目标函数"""
            synthetic = (factor_data * weights).sum(axis=1)
            if method == "max_ic":
                return -synthetic.corr(returns)  # 负相关，因为是最小化
            elif method == "max_sharpe":
                ret = synthetic.mean() / synthetic.std() if synthetic.std() > 0 else 0
                return -ret
            elif method == "min_volatility":
                return synthetic.std()
            return 0

        # 约束：权重和为1
        constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}

        # 边界：权重在[0, 1]之间
        bounds = [(0, 1) for _ in range(n)]

        # 初始权重
        x0 = np.ones(n) / n

        # 优化
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)

        # 获取最优权重
        weights = result.x
        weights = {col: w for col, w in zip(factor_cols, weights)}

        # 计算合成因子
        synthetic = pd.Series(0, index=data.index)
        synthetic.loc[valid_idx] = (factor_data * weights).sum(axis=1)

        # 计算优化后的IC
        ic_after = synthetic[valid_idx].corr(returns[valid_idx])

        return SynthesisResult(
            method="optimize",
            weights=weights,
            ic_before=0,
            ic_after=ic_after,
            factor_values=synthetic,
        )

    def blend(
        self,
        data: pd.DataFrame,
        factor_cols: List[str],
        forward_return_col: str = "forward_return",
        methods: List[str] = None,
        blend_weights: List[float] = None,
    ) -> SynthesisResult:
        """
        多方法混合合成

        Args:
            data: 包含因子和收益数据
            factor_cols: 因子列列表
            forward_return_col: 未来收益列
            methods: 合成方法列表 ["equal", "ic_ir", "pca", "optimize"]
            blend_weights: 混合权重

        Returns:
            SynthesisResult
        """
        if methods is None:
            methods = ["equal", "ic_ir", "optimize"]

        if blend_weights is None:
            blend_weights = [1.0 / len(methods)] * len(methods)

        # 归一化混合权重
        total = sum(blend_weights)
        blend_weights = [w / total for w in blend_weights]

        # 计算各方法的合成因子
        synthetic_factors = []

        for method in methods:
            if method == "equal":
                result = self.equal_weight(data, factor_cols)
            elif method == "ic_ir":
                result = self.ic_ir_weight(data, factor_cols, forward_return_col)
            elif method == "pca":
                result = self.pca_weight(data, factor_cols)
            elif method == "optimize":
                result = self.optimize_weight(data, factor_cols, forward_return_col)
            else:
                continue

            synthetic_factors.append(result.factor_values)

        # 混合
        blended = pd.Series(0, index=data.index)
        for synthetic, weight in zip(synthetic_factors, blend_weights):
            blended += synthetic.fillna(0) * weight

        return SynthesisResult(
            method="blend",
            weights={},
            ic_before=0,
            ic_after=0,
            factor_values=blended,
        )


# ========== 便捷函数 ==========


def synthesize_factors(
    data: pd.DataFrame,
    factor_cols: List[str],
    method: str = "equal",
    forward_return_col: str = "forward_return",
) -> pd.Series:
    """
    快速因子合成

    Args:
        data: 数据
        factor_cols: 因子列列表
        method: 合成方法 "equal", "ic", "ic_ir", "pca", "optimize"
        forward_return_col: 未来收益列

    Returns:
        合成后的因子值
    """
    synthesizer = FactorSynthesizer()

    if method == "equal":
        result = synthesizer.equal_weight(data, factor_cols)
    elif method == "ic":
        result = synthesizer.ic_weight(data, factor_cols, forward_return_col)
    elif method == "ic_ir":
        result = synthesizer.ic_ir_weight(data, factor_cols, forward_return_col)
    elif method == "pca":
        result = synthesizer.pca_weight(data, factor_cols)
    elif method == "optimize":
        result = synthesizer.optimize_weight(data, factor_cols, forward_return_col)
    else:
        raise ValueError(f"Unknown method: {method}")

    return result.factor_values


__all__ = [
    "SynthesisResult",
    "FactorSynthesizer",
    "synthesize_factors",
]
