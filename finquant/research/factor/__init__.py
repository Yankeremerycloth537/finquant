"""
finquant - 因子研究模块
"""

from finquant.research.factor.ic_analysis import (
    ICResult,
    FactorICAnalyzer,
    GroupICAnalyzer,
    calc_ic,
    calc_rank_ic,
    analyze_factors,
)

from finquant.research.factor.backtest import (
    GroupResult,
    BacktestResult,
    FactorBacktest,
    RollingGroupBacktest,
    factor_backtest,
)

from finquant.research.factor.correlation import (
    CorrelationResult,
    FactorCorrelation,
    RollingCorrelation,
    FactorOrthogonalizer,
    factor_correlation,
    orthogonalize_factor,
)

from finquant.research.factor.synthesizer import (
    SynthesisResult,
    FactorSynthesizer,
    synthesize_factors,
)

__all__ = [
    # IC分析
    "ICResult",
    "FactorICAnalyzer",
    "GroupICAnalyzer",
    "calc_ic",
    "calc_rank_ic",
    "analyze_factors",
    # 分组回测
    "GroupResult",
    "BacktestResult",
    "FactorBacktest",
    "RollingGroupBacktest",
    "factor_backtest",
    # 相关性分析
    "CorrelationResult",
    "FactorCorrelation",
    "RollingCorrelation",
    "FactorOrthogonalizer",
    "factor_correlation",
    "orthogonalize_factor",
    # 因子合成
    "SynthesisResult",
    "FactorSynthesizer",
    "synthesize_factors",
]
