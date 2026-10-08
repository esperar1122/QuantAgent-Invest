#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuantAgent-Invest 统一单测执行器 (Windows 控制台 UTF-8 编码自适应 Runner)
用法:
    python run_tests.py
"""

import sys
import os
import io
import time
import importlib.util

# 自动处理 Windows 终端 GBK 编码问题，强制标准输出与标准错误为 UTF-8
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    else:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    else:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)


def main():
    print("=" * 70)
    print("🚀 QuantAgent-Invest 全套核心量化交易引擎单测启动中...")
    print("=" * 70)

    start_time = time.time()
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)

        test_file = os.path.join(current_dir, "tests", "test_quant_modules.py")
        spec = importlib.util.spec_from_file_location("local_test_quant_modules", test_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"无法定位测试模块: {test_file}")
        test_quant_modules = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_quant_modules)

        tests = [
            ("性能指标核算引擎 (Performance Calculator)", test_quant_modules.test_performance_calculator),
            ("A股T+1与整手买卖模拟器 (Trade Simulator A-Share Rules)", test_quant_modules.test_trade_simulator_a_share_rules),
            ("滑点模型与摩擦损耗核算 (Slippage & Friction Models)", test_quant_modules.test_trade_simulator_slippage_and_friction_models),
            ("经典量化策略信号生成 (Strategies Signals)", test_quant_modules.test_strategies_signals),
            ("单标的回测全流程引擎 (Backtest Engine)", test_quant_modules.test_backtest_engine_run),
            ("多标的资产组合截面回测与归因看板 (Portfolio Backtest Engine)", test_quant_modules.test_portfolio_backtest_engine),
            ("自定义多指标组合与风控策略 (Custom Rule Strategy)", test_quant_modules.test_custom_rule_strategy),
            ("四大头寸资金管理模型 (Position Sizing Models)", test_quant_modules.test_position_sizing_models),
            ("资产组合动态再平衡优化器 (Portfolio Optimizer)", test_quant_modules.test_portfolio_optimizer),
            ("微信交易信号卡片直推格式化 (WeChat Alert Formatter)", test_quant_modules.test_wechat_notifier_card_formatting),
            ("虚拟模拟盘账户与基础撮合 (Paper Trading Service)", test_quant_modules.test_paper_trading_service),
            ("五档盘口穿透撮合/排队限价挂单/流动性风控 (Paper Trading Depth & Queue)", test_quant_modules.test_paper_trading_depth_queue_and_liquidity),
        ]

        passed = 0
        failed = 0

        for name, test_fn in tests:
            t0 = time.time()
            try:
                test_fn()
                dur = (time.time() - t0) * 1000
                print(f"  [PASS] {name} ({dur:.1f}ms)")
                passed += 1
            except Exception as e:
                dur = (time.time() - t0) * 1000
                print(f"  [FAIL] {name} ({dur:.1f}ms): {e}")
                failed += 1

        total_time = time.time() - start_time
        print("=" * 70)
        if failed == 0:
            print(f"🎉 全部 {passed} 项单元测试 100% 顺利通过！(耗时: {total_time:.2f}s)")
            print("=" * 70)
            sys.exit(0)
        else:
            print(f"❌ 测试失败: {passed} 项通过, {failed} 项未通过！(耗时: {total_time:.2f}s)")
            print("=" * 70)
            sys.exit(1)

    except Exception as e:
        print(f"❌ 运行测试时发生严重未捕获异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
