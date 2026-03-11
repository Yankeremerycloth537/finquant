"""
Tests for analysis module
"""

import pytest
import pandas as pd
import numpy as np
from finquant.result import BacktestResult, calculate_sortino_ratio, calculate_calmar_ratio


class TestRiskIndicators:
    """测试风险指标计算"""

    def test_sortino_ratio(self):
        """测试索提诺比率"""
        returns = [0.01, -0.005, 0.015, 0.02, -0.01]

        sortino = calculate_sortino_ratio(returns)

        assert isinstance(sortino, float)

    def test_calmar_ratio(self):
        """测试卡玛比率"""
        total_return = 0.5
        max_drawdown = 0.2

        calmar = calculate_calmar_ratio(total_return, max_drawdown)

        assert calmar == 2.5

    def test_calmar_ratio_zero_drawdown(self):
        """测试最大回撤为0的情况"""
        total_return = 0.5
        max_drawdown = 0.0

        calmar = calculate_calmar_ratio(total_return, max_drawdown)

        assert calmar == 0.0


class TestBacktestResult:
    """测试回测结果类"""

    def test_backtest_result_creation(self):
        """测试创建回测结果"""
        result = BacktestResult()

        assert result.backtest_id == ""
        assert result.total_return == 0.0

    def test_backtest_result_to_dict(self):
        """测试转换为字典"""
        result = BacktestResult()
        result.backtest_id = "test_001"
        result.total_return = 0.1

        result_dict = result.to_dict()

        assert result_dict['backtest_id'] == 'test_001'
        assert result_dict['total_return'] == 0.1
