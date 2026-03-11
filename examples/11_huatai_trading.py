"""
finquant - 华泰证券实盘交易示例

演示如何使用华泰证券券商适配器
"""

import time


# ========== 示例1：创建华泰券商 ==========

def example_create_huatai_broker():
    """创建华泰证券券商"""
    print("\n" + "="*60)
    print("示例1：创建华泰证券券商")
    print("="*60)

    from finquant import (
        create_huatai_broker,
        HuataiConfig,
        HuataiSimulatedBroker,
    )

    # 方式1: 使用便捷函数 (模拟模式)
    broker = create_huatai_broker(
        account_id="123456789",
        password="password",
        app_key="your_app_key",
        app_secret="your_app_secret",
        initial_cash=100000,
        simulated=True,  # 模拟模式
    )

    # 方式2: 模拟模式 (简化)
    broker = create_huatai_broker(initial_cash=100000)

    # 方式3: 直接创建
    config = HuataiConfig(
        account_id="123456789",
        password="password",
    )
    broker = HuataiSimulatedBroker(config, initial_cash=100000)

    print(f"券商类型: {type(broker).__name__}")
    print(f"初始资金: 100000")


# ========== 示例2：模拟交易 ==========

def example_simulated_trading():
    """模拟交易"""
    print("\n" + "="*60)
    print("示例2：模拟交易")
    print("="*60)

    from finquant import (
        create_huatai_broker,
        get_realtime_quote,
    )

    # 创建模拟券商
    broker = create_huatai_broker(initial_cash=100000)
    broker.initialize()

    # 设置行情
    broker.set_quote("SH600519", 1400.0)

    print(f"\n初始账户:")
    account = broker.get_account()
    print(f"  现金: {account.cash:.2f}")

    # 买入
    print(f"\n--- 买入 SH600519 10股 @ 1400 ---")
    order = broker.buy("SH600519", 10, price=1400)
    print(f"订单ID: {order.order_id}")
    print(f"状态: {order.status.value}")

    account = broker.get_account()
    print(f"\n账户信息:")
    print(f"  现金: {account.cash:.2f}")
    print(f"  持仓数: {len(account.positions)}")

    for pos in account.positions:
        print(f"\n  {pos.code}:")
        print(f"    股数: {pos.shares}")
        print(f"    成本: {pos.avg_cost:.2f}")
        print(f"    当前价: {pos.current_price:.2f}")
        print(f"    盈亏: {pos.profit:.2f} ({pos.profit_ratio*100:.2f}%)")

    # 卖出
    print(f"\n--- 卖出 SH600519 5股 @ 1450 ---")
    broker.set_quote("SH600519", 1450.0)  # 涨价
    order = broker.sell("SH600519", 5, price=1450)
    print(f"订单ID: {order.order_id}")
    print(f"状态: {order.status.value}")

    account = broker.get_account()
    print(f"\n最终账户:")
    print(f"  现金: {account.cash:.2f}")
    print(f"  持仓市值: {account.market_value:.2f}")
    print(f"  总资产: {account.total_assets:.2f}")


# ========== 示例3：真实API模式 ==========

def example_real_api():
    """真实API模式"""
    print("\n" + "="*60)
    print("示例3：真实API模式")
    print("="*60)

    print("""
真实API模式说明:

1. 需要在华泰证券开户
2. 申请量化API权限
3. 获取 App Key 和 App Secret
4. 使用真实API下单

配置示例:
    broker = create_huatai_broker(
        account_id="你的资金账号",
        password="你的交易密码",
        app_key="申请的AppKey",
        app_secret="申请的AppSecret",
        simulated=False,  # 真实API
    )

注意事项:
- 真实API需要网络连接华泰服务器
- 下单会真实扣除资金
- 请务必在测试环境验证后再实盘

华泰量化平台: https://quant.xinguanyao.com/
    """)


# ========== 示例4：信号转实盘 ==========

def example_signal_trading():
    """信号转实盘"""
    print("\n" + "="*60)
    print("示例4：信号转实盘")
    print("="*60)

    from finquant import (
        Signal, Action,
        buy_signal, sell_signal,
        SignalBus,
        create_huatai_broker,
    )

    # 创建券商
    broker = create_huatai_broker(initial_cash=100000)
    broker.initialize()

    # 设置初始行情
    broker.set_quote("SH600519", 1400.0)
    broker.set_quote("SZ000001", 10.0)

    # 信号处理器
    def signal_to_order(signal: Signal, context: dict):
        print(f"\n收到信号: {signal.action.value} {signal.code}")

        # 获取当前价格
        price = broker.get_quote(signal.code)
        if not price:
            price = 10.0

        if signal.action == Action.BUY:
            # 买入可用资金的 20%
            account = broker.get_account()
            quantity = int(account.cash * 0.2 / price / 100) * 100

            if quantity > 0:
                order = broker.buy(signal.code, quantity, price=price)
                print(f"  -> 买入: {order.quantity}股 @ {order.avg_price}")
            else:
                print(f"  -> 资金不足")

        elif signal.action == Action.SELL:
            positions = broker.get_positions()
            for pos in positions:
                if pos.code == signal.code and pos.shares > 0:
                    order = broker.sell(signal.code, pos.shares, price=price)
                    print(f"  -> 卖出: {order.quantity}股 @ {order.avg_price}")
                    break

    # 创建信号总线
    bus = SignalBus()
    bus.subscribe(signal_to_order)

    # 发布信号
    print("--- 测试买入信号 ---")
    bus.publish(buy_signal(code="SH600519", reason="MA金叉"))

    print("\n--- 测试卖出信号 ---")
    bus.publish(sell_signal(code="SH600519", reason="MA死叉"))

    # 查看账户
    account = broker.get_account()
    print(f"\n--- 最终账户 ---")
    print(f"现金: {account.cash:.2f}")
    print(f"持仓市值: {account.market_value:.2f}")
    print(f"总资产: {account.total_assets:.2f}")


# ========== 示例5：策略实盘运行 ==========

def example_strategy_live():
    """策略实盘运行"""
    print("\n" + "="*60)
    print("示例5：策略实盘运行")
    print("="*60)

    print("""
实盘策略运行框架:

    from finquant import (
        create_huatai_broker,
        create_simulated_broker,
        get_realtime_quote,
    )

    # 选择券商
    broker = create_huatai_broker(initial_cash=100000)  # 华泰模拟
    # 或
    broker = create_simulated_broker(initial_cash=100000)  # 东财行情

    broker.initialize()

    # 策略参数
    codes = ["SH600519", "SZ000001"]

    while True:
        # 1. 获取行情
        quotes = get_realtime_quote(codes)

        # 2. 你的策略逻辑
        signals = run_strategy(quotes)

        # 3. 执行信号
        for signal in signals:
            execute_signal(broker, signal)

        # 4. 更新行情到券商
        for code, quote in quotes.items():
            broker.set_quote(code, quote.get("price", 0))

        # 5. 打印账户
        account = broker.get_account()
        print(f"总资产: {account.total_assets:.2f}")

        time.sleep(60)  # 每分钟执行一次

运行命令:
    python examples/11_huatai_trading.py
    # 然后选择运行示例5
    """)


# ========== 运行示例 ==========

if __name__ == "__main__":
    print("="*60)
    print("finquant 华泰证券实盘示例")
    print("="*60)

    example_create_huatai_broker()
    example_simulated_trading()
    example_real_api()
    example_signal_trading()
    example_strategy_live()
