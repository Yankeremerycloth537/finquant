"""
finquant - 策略研究环境

提供完整的因子研究和策略分析功能：
- 因子IC分析 (FactorICAnalyzer)
- 因子分组回测 (FactorBacktest)
- 因子相关性分析 (FactorCorrelation)
- 因子合成 (FactorSynthesizer)
- 量化研究实验室 (QuantLab)
"""

from finquant.research.factor import (
    # IC分析
    ICResult,
    FactorICAnalyzer,
    GroupICAnalyzer,
    calc_ic,
    calc_rank_ic,
    analyze_factors,
    # 分组回测
    GroupResult,
    BacktestResult,
    FactorBacktest,
    RollingGroupBacktest,
    factor_backtest,
    # 相关性分析
    CorrelationResult,
    FactorCorrelation,
    RollingCorrelation,
    FactorOrthogonalizer,
    factor_correlation,
    orthogonalize_factor,
    # 因子合成
    SynthesisResult,
    FactorSynthesizer,
    synthesize_factors,
)

from finquant.research.lab import (
    LabConfig,
    FactorStudyResult,
    BacktestStudyResult,
    QuantLab,
    create_lab,
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
    # QuantLab
    "LabConfig",
    "FactorStudyResult",
    "BacktestStudyResult",
    "QuantLab",
    "create_lab",
]
