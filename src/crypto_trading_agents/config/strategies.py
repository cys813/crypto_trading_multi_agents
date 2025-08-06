"""
策略配置文件

定义各种交易策略的参数和配置
"""

# 技术分析策略配置
TECHNICAL_STRATEGIES = {
    "moving_average_crossover": {
        "name": "移动平均线交叉策略",
        "type": "trend_following",
        "timeframes": ["1h", "4h", "1d"],
        "parameters": {
            "fast_ma": 10,
            "slow_ma": 30,
            "signal_ma": 9,
            "ma_type": "EMA",  # SMA, EMA, WMA
        },
        "entry_conditions": {
            "long": "fast_ma > slow_ma and fast_ma > signal_ma",
            "short": "fast_ma < slow_ma and fast_ma < signal_ma",
        },
        "exit_conditions": {
            "long": "fast_ma < slow_ma or price < stop_loss",
            "short": "fast_ma > slow_ma or price > take_profit",
        },
        "risk_management": {
            "stop_loss": 0.02,
            "take_profit": 0.06,
            "position_size": 0.1,
            "max_leverage": 3,
        },
        "performance_metrics": {
            "expected_win_rate": 0.65,
            "profit_factor": 1.8,
            "max_drawdown": 0.15,
        }
    },
    "rsi_oversold_overbought": {
        "name": "RSI超买超卖策略",
        "type": "mean_reversion",
        "timeframes": ["1h", "4h"],
        "parameters": {
            "rsi_period": 14,
            "oversold_threshold": 30,
            "overbought_threshold": 70,
            "rsi_smoothing": "Wilder",
        },
        "entry_conditions": {
            "long": "rsi < oversold_threshold and price > support",
            "short": "rsi > overbought_threshold and price < resistance",
        },
        "exit_conditions": {
            "long": "rsi > 50 or price > take_profit",
            "short": "rsi < 50 or price < stop_loss",
        },
        "risk_management": {
            "stop_loss": 0.015,
            "take_profit": 0.03,
            "position_size": 0.08,
            "max_leverage": 2,
        },
        "performance_metrics": {
            "expected_win_rate": 0.7,
            "profit_factor": 1.5,
            "max_drawdown": 0.1,
        }
    },
    "bollinger_bands_breakout": {
        "name": "布林带突破策略",
        "type": "volatility_breakout",
        "timeframes": ["1h", "4h"],
        "parameters": {
            "bb_period": 20,
            "bb_std": 2,
            "rsi_period": 14,
            "volume_confirmation": True,
        },
        "entry_conditions": {
            "long": "price > upper_band and rsi > 50 and volume > avg_volume",
            "short": "price < lower_band and rsi < 50 and volume > avg_volume",
        },
        "exit_conditions": {
            "long": "price < middle_band or rsi < 30",
            "short": "price > middle_band or rsi > 70",
        },
        "risk_management": {
            "stop_loss": 0.025,
            "take_profit": 0.05,
            "position_size": 0.12,
            "max_leverage": 3,
        },
        "performance_metrics": {
            "expected_win_rate": 0.6,
            "profit_factor": 1.6,
            "max_drawdown": 0.18,
        }
    },
    "macd_divergence": {
        "name": "MACD背离策略",
        "type": "momentum",
        "timeframes": ["4h", "1d"],
        "parameters": {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9,
            "rsi_period": 14,
        },
        "entry_conditions": {
            "long": "price makes lower low but MACD makes higher low and rsi < 30",
            "short": "price makes higher high but MACD makes lower high and rsi > 70",
        },
        "exit_conditions": {
            "long": "macd crosses below signal line or price > take_profit",
            "short": "macd crosses above signal line or price < stop_loss",
        },
        "risk_management": {
            "stop_loss": 0.03,
            "take_profit": 0.08,
            "position_size": 0.1,
            "max_leverage": 2,
        },
        "performance_metrics": {
            "expected_win_rate": 0.55,
            "profit_factor": 2.0,
            "max_drawdown": 0.2,
        }
    }
}

# 链上分析策略配置
ONCHAIN_STRATEGIES = {
    "exchange_flow_analysis": {
        "name": "交易所流量分析策略",
        "type": "flow_analysis",
        "timeframes": ["1d"],
        "parameters": {
            "flow_threshold": 0.1,  # 10% of supply
            "lookback_period": 30,
            "smoothing_period": 7,
        },
        "entry_conditions": {
            "long": "net_outflow > threshold and price > 200ma",
            "short": "net_inflow > threshold and price < 200ma",
        },
        "exit_conditions": {
            "long": "net_inflow > threshold or profit_target_reached",
            "short": "net_outflow > threshold or loss_limit_reached",
        },
        "risk_management": {
            "stop_loss": 0.04,
            "take_profit": 0.12,
            "position_size": 0.15,
            "max_leverage": 2,
        },
        "performance_metrics": {
            "expected_win_rate": 0.7,
            "profit_factor": 2.2,
            "max_drawdown": 0.15,
        }
    },
    "whale_accumulation": {
        "name": "巨鲸积累策略",
        "type": "smart_money",
        "timeframes": ["1d", "1w"],
        "parameters": {
            "whale_threshold": 100,  # BTC数量
            "accumulation_period": 14,
            "price_threshold": 0.05,
        },
        "entry_conditions": {
            "long": "whale_accumulation > threshold and price_change < threshold and rsi < 50",
        },
        "exit_conditions": {
            "long": "whale_distribution > threshold or profit_target_reached",
        },
        "risk_management": {
            "stop_loss": 0.05,
            "take_profit": 0.15,
            "position_size": 0.2,
            "max_leverage": 1,
        },
        "performance_metrics": {
            "expected_win_rate": 0.8,
            "profit_factor": 2.5,
            "max_drawdown": 0.1,
        }
    },
    "network_health": {
        "name": "网络健康策略",
        "type": "fundamental",
        "timeframes": ["1d", "1w"],
        "parameters": {
            "active_addresses_threshold": 0.1,
            "hash_rate_threshold": 0.05,
            "fee_threshold": 0.2,
        },
        "entry_conditions": {
            "long": "active_addresses_growth > threshold and hash_rate_growth > threshold and fees < historical_average",
        },
        "exit_conditions": {
            "long": "network_metrics_deteriorate or profit_target_reached",
        },
        "risk_management": {
            "stop_loss": 0.06,
            "take_profit": 0.2,
            "position_size": 0.1,
            "max_leverage": 1,
        },
        "performance_metrics": {
            "expected_win_rate": 0.75,
            "profit_factor": 2.0,
            "max_drawdown": 0.12,
        }
    }
}

# 情绪分析策略配置
SENTIMENT_STRATEGIES = {
    "fear_greed_contrarian": {
        "name": "恐惧贪婪逆向策略",
        "type": "contrarian",
        "timeframes": ["1d"],
        "parameters": {
            "extreme_fear_threshold": 20,
            "extreme_greed_threshold": 80,
            "lookback_period": 30,
        },
        "entry_conditions": {
            "long": "fear_greed_index < extreme_fear_threshold and price > support",
            "short": "fear_greed_index > extreme_greed_threshold and price < resistance",
        },
        "exit_conditions": {
            "long": "fear_greed_index > 50 or profit_target_reached",
            "short": "fear_greed_index < 50 or loss_limit_reached",
        },
        "risk_management": {
            "stop_loss": 0.03,
            "take_profit": 0.1,
            "position_size": 0.12,
            "max_leverage": 2,
        },
        "performance_metrics": {
            "expected_win_rate": 0.65,
            "profit_factor": 1.8,
            "max_drawdown": 0.15,
        }
    },
    "social_volume_momentum": {
        "name": "社交量动量策略",
        "type": "momentum",
        "timeframes": ["1h", "4h"],
        "parameters": {
            "volume_threshold": 2.0,  # 相对于平均值的倍数
            "sentiment_threshold": 0.6,
            "price_confirmation": True,
        },
        "entry_conditions": {
            "long": "social_volume > threshold * avg_volume and sentiment_score > sentiment_threshold and price > 20ma",
            "short": "social_volume > threshold * avg_volume and sentiment_score < (1 - sentiment_threshold) and price < 20ma",
        },
        "exit_conditions": {
            "long": "social_volume < avg_volume or sentiment_score < 0.4",
            "short": "social_volume < avg_volume or sentiment_score > 0.6",
        },
        "risk_management": {
            "stop_loss": 0.025,
            "take_profit": 0.075,
            "position_size": 0.1,
            "max_leverage": 2,
        },
        "performance_metrics": {
            "expected_win_rate": 0.6,
            "profit_factor": 1.6,
            "max_drawdown": 0.18,
        }
    }
}

# DeFi策略配置
DEFI_STRATEGIES = {
    "tvl_momentum": {
        "name": "TVL动量策略",
        "type": "fundamental",
        "timeframes": ["1d", "1w"],
        "parameters": {
            "tvl_threshold": 0.1,  # 10% change
            "lookback_period": 30,
            "market_cap_threshold": 100000000,  # 1亿美元
        },
        "entry_conditions": {
            "long": "protocol_tvl_growth > threshold and market_cap > threshold and price_trend > 0",
        },
        "exit_conditions": {
            "long": "tvl_growth < 0 or profit_target_reached",
        },
        "risk_management": {
            "stop_loss": 0.08,
            "take_profit": 0.25,
            "position_size": 0.05,
            "max_leverage": 1,
        },
        "performance_metrics": {
            "expected_win_rate": 0.7,
            "profit_factor": 2.5,
            "max_drawdown": 0.2,
        }
    },
    "yield_farming_opportunity": {
        "name": "挖矿收益机会策略",
        "type": "arbitrage",
        "timeframes": ["1d"],
        "parameters": {
            "apy_threshold": 0.2,  # 20% APY
            "risk_threshold": 0.3,
            "tvl_stability": 0.1,
        },
        "entry_conditions": {
            "long": "pool_apy > threshold and risk_score < risk_threshold and tvl_stability < stability_threshold",
        },
        "exit_conditions": {
            "long": "apy < threshold * 0.5 or risk_score > risk_threshold * 1.5",
        },
        "risk_management": {
            "stop_loss": 0.1,
            "take_profit": 0.3,
            "position_size": 0.03,
            "max_leverage": 1,
        },
        "performance_metrics": {
            "expected_win_rate": 0.8,
            "profit_factor": 3.0,
            "max_drawdown": 0.15,
        }
    }
}

# 量化策略配置
QUANTITATIVE_STRATEGIES = {
    "statistical_arbitrage": {
        "name": "统计套利策略",
        "type": "arbitrage",
        "timeframes": ["1m", "5m", "15m"],
        "parameters": {
            "lookback_period": 100,
            "z_score_threshold": 2.0,
            "correlation_threshold": 0.8,
            "pairs": ["BTC/ETH", "SOL/AVAX", "MATIC/DOT"],
        },
        "entry_conditions": {
            "long": "z_score < -threshold and correlation > correlation_threshold",
            "short": "z_score > threshold and correlation > correlation_threshold",
        },
        "exit_conditions": {
            "long": "z_score > 0 or profit_target_reached",
            "short": "z_score < 0 or loss_limit_reached",
        },
        "risk_management": {
            "stop_loss": 0.01,
            "take_profit": 0.02,
            "position_size": 0.05,
            "max_leverage": 5,
        },
        "performance_metrics": {
            "expected_win_rate": 0.75,
            "profit_factor": 1.8,
            "max_drawdown": 0.05,
        }
    },
    "mean_reversion_pairs": {
        "name": "均值回归配对策略",
        "type": "statistical",
        "timeframes": ["1h", "4h"],
        "parameters": {
            "half_life": 30,
            "entry_threshold": 2.0,
            "exit_threshold": 0.5,
            "pairs": ["BTC/ETH", "SOL/AVAX"],
        },
        "entry_conditions": {
            "long": "spread_ratio < -entry_threshold",
            "short": "spread_ratio > entry_threshold",
        },
        "exit_conditions": {
            "long": "spread_ratio > -exit_threshold",
            "short": "spread_ratio < exit_threshold",
        },
        "risk_management": {
            "stop_loss": 0.015,
            "take_profit": 0.03,
            "position_size": 0.08,
            "max_leverage": 3,
        },
        "performance_metrics": {
            "expected_win_rate": 0.7,
            "profit_factor": 1.6,
            "max_drawdown": 0.08,
        }
    }
}

# 策略组合配置
STRATEGY_PORTFOLIOS = {
    "conservative": {
        "name": "保守组合",
        "risk_level": "low",
        "strategies": {
            "moving_average_crossover": 0.3,
            "network_health": 0.3,
            "fear_greed_contrarian": 0.2,
            "tvl_momentum": 0.2,
        },
        "allocation": {
            "technical": 0.3,
            "onchain": 0.3,
            "sentiment": 0.2,
            "defi": 0.2,
        },
        "risk_parameters": {
            "max_portfolio_risk": 0.1,
            "max_position_size": 0.05,
            "max_leverage": 1,
            "stop_loss": 0.02,
        }
    },
    "balanced": {
        "name": "平衡组合",
        "risk_level": "medium",
        "strategies": {
            "moving_average_crossover": 0.2,
            "rsi_oversold_overbought": 0.15,
            "bollinger_bands_breakout": 0.15,
            "exchange_flow_analysis": 0.15,
            "social_volume_momentum": 0.15,
            "yield_farming_opportunity": 0.1,
            "statistical_arbitrage": 0.1,
        },
        "allocation": {
            "technical": 0.5,
            "onchain": 0.15,
            "sentiment": 0.15,
            "defi": 0.05,
            "quantitative": 0.15,
        },
        "risk_parameters": {
            "max_portfolio_risk": 0.15,
            "max_position_size": 0.08,
            "max_leverage": 2,
            "stop_loss": 0.025,
        }
    },
    "aggressive": {
        "name": "激进组合",
        "risk_level": "high",
        "strategies": {
            "bollinger_bands_breakout": 0.2,
            "macd_divergence": 0.15,
            "whale_accumulation": 0.15,
            "social_volume_momentum": 0.15,
            "yield_farming_opportunity": 0.15,
            "statistical_arbitrage": 0.15,
            "mean_reversion_pairs": 0.05,
        },
        "allocation": {
            "technical": 0.35,
            "onchain": 0.15,
            "sentiment": 0.15,
            "defi": 0.15,
            "quantitative": 0.2,
        },
        "risk_parameters": {
            "max_portfolio_risk": 0.25,
            "max_position_size": 0.12,
            "max_leverage": 3,
            "stop_loss": 0.03,
        }
    }
}

# 策略优化配置
STRATEGY_OPTIMIZATION = {
    "parameter_ranges": {
        "moving_average_crossover": {
            "fast_ma": [5, 10, 15, 20],
            "slow_ma": [20, 30, 40, 50],
            "signal_ma": [5, 9, 12, 15],
        },
        "rsi_oversold_overbought": {
            "rsi_period": [7, 14, 21],
            "oversold_threshold": [20, 25, 30, 35],
            "overbought_threshold": [65, 70, 75, 80],
        }
    },
    "optimization_goals": {
        "sharpe_ratio": "maximize",
        "profit_factor": "maximize",
        "max_drawdown": "minimize",
        "win_rate": "maximize",
    },
    "backtesting_config": {
        "start_date": "2020-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 100000,
        "commission": 0.001,
        "slippage": 0.0005,
    }
}

# 策略监控配置
STRATEGY_MONITORING = {
    "performance_metrics": [
        "total_return",
        "sharpe_ratio",
        "sortino_ratio",
        "max_drawdown",
        "win_rate",
        "profit_factor",
        "calmar_ratio",
        "beta",
        "alpha",
    ],
    "risk_metrics": [
        "var_95",
        "var_99",
        "expected_shortfall",
        "downside_deviation",
        "upside_deviation",
        "information_ratio",
    ],
    "alert_thresholds": {
        "drawdown_alert": 0.1,
        "var_breach_alert": 0.05,
        "performance_decline_alert": 0.15,
        "correlation_alert": 0.8,
    },
    "reporting_frequency": {
        "daily_report": True,
        "weekly_report": True,
        "monthly_report": True,
        "quarterly_report": True,
    }
}