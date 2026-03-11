"""
Tests for limit up/down and suspension handling
"""

import pytest
import pandas as pd
from finquant.core import BacktestEngineV2, BacktestConfig


# 使用新的 API 创建引擎
def create_engine(**kwargs):
    config = BacktestConfig(**kwargs)
    return BacktestEngineV2(config)


class TestLimitUpDown:
    """测试涨跌停处理"""

    def test_limit_up_prevents_buy(self, limit_up_data):
        """测试涨停时禁止买入"""
        class BuyOnLimitUpStrategy:
            """尝试在涨停日买入的策略"""
            def generate_signals(self, data, code, current_date):
                return 1  # 始终买入

        pytest.skip("Limit up/down not implemented in V2 engine")

    def test_limit_down_allows_sell(self, limit_up_data):
        """测试跌停时允许卖出"""
        pytest.skip("Limit up/down not implemented in V2 engine")

    def test_limit_up_disabled(self, limit_up_data):
        """测试禁用涨跌停限制"""
        pytest.skip("Limit up/down not implemented in V2 engine")


class TestSuspension:
    """测试停牌处理"""

    def test_suspended_prevents_trading(self, suspended_data):
        """测试停牌时禁止交易"""
        pytest.skip("Suspension handling not implemented in V2 engine")

    def test_suspension_disabled(self, suspended_data):
        """测试禁用停牌检查"""
        pytest.skip("Suspension handling not implemented in V2 engine")


class TestMarketStatus:
    """测试市场状态识别"""

    def test_is_limit_up(self):
        """测试涨停识别"""
        pytest.skip("Market status not implemented in V2 engine")

    def test_is_limit_down(self):
        """测试跌停识别"""
        pytest.skip("Market status not implemented in V2 engine")

    def test_is_suspended(self):
        """测试停牌识别"""
        pytest.skip("Market status not implemented in V2 engine")
