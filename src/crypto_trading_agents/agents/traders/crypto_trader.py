"""
加密货币交易员 - 执行交易策略和风险管理

基于原版交易架构，针对加密货币市场特征优化
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
from enum import Enum

from src.crypto_trading_agents.services.ai_analysis_mixin import StandardAIAnalysisMixin

logger = logging.getLogger(__name__)

class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"

class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"

class PositionStatus(Enum):
    """持仓状态"""
    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"

class CryptoTrader(StandardAIAnalysisMixin):
    """加密货币交易员 - AI增强版本"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化加密货币交易员
        
        Args:
            config: 配置字典
        """
        super().__init__()
        self.config = config
        self.trading_config = config.get("trading_config", {})
        self.risk_config = config.get("risk_config", {})
        
        # 初始化统一LLM服务
        from src.crypto_trading_agents.services.llm_service import initialize_llm_service
        from src.crypto_trading_agents.config.ai_analysis_config import get_unified_llm_service_config
        
        llm_config = get_unified_llm_service_config()
        initialize_llm_service(llm_config)
        
        # 交易参数配置
        self.max_position_size = self.trading_config.get("max_position_size", 0.1)
        self.risk_per_trade = self.risk_config.get("risk_per_trade", 0.02)
        self.max_leverage = self.trading_config.get("max_leverage", 3)
        self.max_concurrent_trades = self.trading_config.get("max_concurrent_trades", 5)
        
        # 交易状态
        self.current_positions = {}
        self.open_orders = []
        self.trade_history = []
        self.performance_metrics = {}
        
        # 支持的交易策略
        self.trading_strategies = self.trading_config.get("strategies", ["trend_following", "mean_reversion"])
    
    def collect_data(self, symbol: str, end_date: str) -> Dict[str, Any]:
        """
        收集交易决策数据
        
        Args:
            symbol: 交易对符号
            end_date: 截止日期
            
        Returns:
            交易决策数据
        """
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            start_dt = end_dt - timedelta(days=1)  # 交易决策通常用近期数据
            
            return {
                "symbol": symbol,
                "start_date": start_dt.strftime("%Y-%m-%d"),
                "end_date": end_date,
                "market_data": self._collect_market_data(symbol),
                "order_book_data": self._collect_order_book_data(symbol),
                "account_info": self._collect_account_info(),
                "position_info": self._collect_position_info(symbol),
                "risk_metrics": self._collect_risk_metrics(symbol),
            }
            
        except Exception as e:
            logger.error(f"Error collecting trading data for {symbol}: {str(e)}")
            return {"error": str(e)}
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析交易数据并生成交易决策 - AI增强版本
        
        Args:
            data: 交易决策数据
            
        Returns:
            交易分析结果（包含AI增强决策）
        """
        try:
            if "error" in data:
                return {"error": data["error"]}
            
            # 执行传统交易分析
            traditional_analysis = self._perform_traditional_trading_analysis(data)
            
            # 使用AI增强交易决策
            return self.analyze_with_ai_enhancement(
                data, 
                lambda raw_data: traditional_analysis
            )
            
        except Exception as e:
            logger.error(f"Error analyzing trading data: {str(e)}")
            return {"error": str(e)}
    
    def execute_trade(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行交易（基于AI增强分析）
        
        Args:
            analysis: AI增强交易分析结果
            
        Returns:
            交易执行结果
        """
        try:
            # 获取最终交易建议
            final_recommendation = analysis.get("final_recommendation", {})
            action = final_recommendation.get("action", "hold")
            confidence = final_recommendation.get("confidence", 0.0)
            
            # 检查执行条件
            execution_check = self._assess_execution_readiness(analysis)
            if not execution_check.get("ready", False):
                return {
                    "status": "not_executed",
                    "reason": execution_check.get("reason", "Execution conditions not met"),
                    "analysis": analysis,
                }
            
            # 生成交易计划
            trading_plan = self._generate_trading_plan(analysis)
            
            # 执行交易
            if action == "buy" and confidence > 0.6:
                execution_result = self._execute_entry_orders(trading_plan, "buy")
            elif action == "sell" and confidence > 0.6:
                execution_result = self._execute_entry_orders(trading_plan, "sell")
            else:
                execution_result = {"status": "hold", "reason": "Low confidence or hold signal"}
            
            # 设置止损和止盈
            if execution_result.get("status") == "executed":
                self._execute_stop_orders(trading_plan)
                self._execute_take_profit_orders(trading_plan)
            
            # 更新交易历史
            self._update_trade_history(execution_result, analysis)
            
            return {
                **execution_result,
                "trading_plan": trading_plan,
                "execution_timestamp": datetime.now().isoformat(),
                "analysis_summary": {
                    "action": action,
                    "confidence": confidence,
                    "ai_enhanced": analysis.get("analysis_type") == "ai_enhanced_trading",
                },
            }
            
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            return {"error": str(e)}
    
    def _perform_traditional_trading_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行传统的交易分析
        
        Args:
            data: 交易决策数据
            
        Returns:
            传统交易分析结果
        """
        market_data = data.get("market_data", {})
        order_book_data = data.get("order_book_data", {})
        account_info = data.get("account_info", {})
        position_info = data.get("position_info", {})
        risk_metrics = data.get("risk_metrics", {})
        
        # 分析市场条件
        market_conditions = self._analyze_market_conditions(market_data, order_book_data)
        
        # 分析账户状态
        account_status = self._analyze_account_status(account_info)
        
        # 分析当前持仓
        position_analysis = self._analyze_positions(position_info)
        
        # 生成交易信号
        trading_signals = self._generate_trading_signals(market_conditions, account_status, position_analysis)
        
        # 做出交易决策
        trading_decision = self._make_trading_decision(trading_signals, risk_metrics)
        
        # 评估交易风险
        trading_risks = self._assess_trading_risks(trading_decision, risk_metrics)
        
        return {
            "market_conditions": market_conditions,
            "account_status": account_status,
            "position_analysis": position_analysis,
            "trading_signals": trading_signals,
            "trading_decision": trading_decision,
            "trading_risks": trading_risks,
            "confidence": self._calculate_confidence(trading_signals),
            "execution_readiness": self._assess_execution_readiness({
                "trading_decision": trading_decision,
                "trading_risks": trading_risks
            }),
        }
    
    def _build_trading_analysis_prompt(self, raw_data: Dict[str, Any], traditional_analysis: Dict[str, Any]) -> str:
        """
        构建交易分析的AI提示词
        
        Args:
            raw_data: 原始数据
            traditional_analysis: 传统分析结果
            
        Returns:
            AI分析提示词
        """
        symbol = raw_data.get("symbol", "Unknown")
        
        # 市场条件摘要
        market_conditions = traditional_analysis.get("market_conditions", {})
        market_trend = market_conditions.get("trend", "neutral")
        market_volatility = market_conditions.get("volatility", "normal")
        
        # 账户状态摘要
        account_status = traditional_analysis.get("account_status", {})
        available_balance = account_status.get("available_balance", 0)
        current_exposure = account_status.get("current_exposure", 0)
        
        # 交易信号摘要
        trading_signals = traditional_analysis.get("trading_signals", {})
        signal_strength = trading_signals.get("overall_strength", 0.5)
        signal_direction = trading_signals.get("direction", "neutral")
        
        # 传统交易决策
        trading_decision = traditional_analysis.get("trading_decision", {})
        recommended_action = trading_decision.get("action", "hold")
        position_size = trading_decision.get("position_size", 0)
        
        # 风险评估
        trading_risks = traditional_analysis.get("trading_risks", {})
        risk_level = trading_risks.get("risk_level", "medium")
        
        prompt = f"""
作为专业的加密货币AI交易专家，请基于以下传统交易分析结果提供深度AI增强交易决策：

## 交易对信息
- 符号: {symbol}
- 分析时间: {raw_data.get('end_date', 'Unknown')}

## 传统交易分析结果摘要

### 市场条件分析
- 市场趋势: {market_trend}
- 市场波动性: {market_volatility}
- 市场情绪: {market_conditions.get('sentiment', 'neutral')}

### 账户状态分析
- 可用余额: ${available_balance:,.2f}
- 当前风险暴露: {current_exposure:.2%}
- 杠杆使用率: {account_status.get('leverage_usage', 0):.2%}

### 交易信号分析
- 信号方向: {signal_direction}
- 信号强度: {signal_strength:.3f}
- 技术指标汇总: {len(trading_signals.get('technical_signals', []))}个指标

### 传统交易决策
- 推荐操作: {recommended_action}
- 建议仓位: {position_size:.2%}
- 风险等级: {risk_level}

## 请提供以下AI增强交易决策分析

### 1. 智能市场时机分析
- 基于多维度数据分析最佳入场/出场时机
- 识别可能的市场转折点和关键支撑阻力位
- 评估当前市场微观结构对交易的影响

### 2. 动态仓位管理建议
- 基于风险预算和波动性调整最优仓位大小
- 推荐分批建仓/平仓策略
- 动态止损止盈位设置建议

### 3. 风险收益优化
- 基于历史数据和当前条件计算期望收益率
- 评估风险调整后收益的可行性
- 识别潜在的风险因素和对冲策略

### 4. 多策略协同决策
- 整合趋势跟踪、均值回归等多种策略信号
- 基于市场状态选择最适合的交易策略
- 评估策略切换的最佳时机

### 5. 心理偏差纠正
- 识别可能的认知偏差和情绪化决策
- 提供客观的交易逻辑验证
- 建议风险管理的心理准备

### 6. 最终交易建议
- 综合AI分析的最终交易建议 (买入/卖出/持有)
- 具体的执行计划和时间安排
- 关键监控指标和退出条件

请以JSON格式返回分析结果，确保包含具体的数值和可执行的交易建议。
"""
        return prompt
    
    def _combine_trading_analyses(self, traditional_analysis: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        整合传统交易分析和AI分析结果
        
        Args:
            traditional_analysis: 传统交易分析结果
            ai_analysis: AI交易分析结果
            
        Returns:
            整合后的交易分析结果
        """
        # 整合置信度
        traditional_confidence = traditional_analysis.get("confidence", 0.3)
        ai_confidence = ai_analysis.get("confidence", 0.3)
        combined_confidence = (traditional_confidence * 0.3 + ai_confidence * 0.7)
        
        # 整合交易决策
        traditional_decision = traditional_analysis.get("trading_decision", {})
        ai_recommendation = ai_analysis.get("trading_recommendation", {})
        
        combined_recommendation = {
            "action": ai_recommendation.get("action", traditional_decision.get("action", "hold")),
            "confidence": combined_confidence,
            "position_size": ai_recommendation.get("position_size", traditional_decision.get("position_size", 0)),
            "entry_price": ai_recommendation.get("entry_price", traditional_decision.get("entry_price", 0)),
            "stop_loss": ai_recommendation.get("stop_loss", traditional_decision.get("stop_loss", 0)),
            "take_profit": ai_recommendation.get("take_profit", traditional_decision.get("take_profit", 0)),
            "traditional_bias": traditional_decision.get("action", "hold"),
            "ai_bias": ai_recommendation.get("action", "hold"),
            "consensus": self._determine_trading_consensus(traditional_decision, ai_recommendation),
        }
        
        # 创建增强洞察
        enhanced_insights = {
            "market_timing": ai_analysis.get("market_timing", {}),
            "position_management": ai_analysis.get("position_management", {}),
            "risk_reward_optimization": ai_analysis.get("risk_reward", {}),
            "strategy_coordination": ai_analysis.get("strategy_coordination", {}),
            "execution_plan": ai_analysis.get("execution_plan", {}),
            "monitoring_alerts": ai_analysis.get("monitoring_alerts", []),
        }
        
        return {
            **traditional_analysis,
            "ai_analysis": ai_analysis,
            "combined_confidence": combined_confidence,
            "final_recommendation": combined_recommendation,
            "enhanced_insights": enhanced_insights,
            "analysis_type": "ai_enhanced_trading",
        }
    
    def _determine_trading_consensus(self, traditional_decision: Dict[str, Any], ai_recommendation: Dict[str, Any]) -> str:
        """确定传统分析和AI分析的交易共识"""
        traditional_action = traditional_decision.get("action", "hold")
        ai_action = ai_recommendation.get("action", "hold")
        
        if traditional_action == ai_action:
            return f"strong_consensus_{traditional_action}"
        else:
            # 检查是否有部分共识（如都不是hold）
            if traditional_action != "hold" and ai_action != "hold":
                return "directional_consensus"
            else:
                return "low_consensus"

    def _collect_market_data(self, symbol: str) -> Dict[str, Any]:
        """收集市场数据"""
        # 模拟市场数据收集
        base_price = 50000 if "BTC" in symbol else 3000
        
        return {
            "current_price": base_price,
            "24h_change": 0.025,  # 2.5%涨幅
            "24h_volume": 1000000000,
            "market_cap": 500000000000,
            "price_history": [base_price * (1 + i * 0.001) for i in range(-10, 1)],
            "volatility": 0.04,
            "trend": "bullish",
        }
    
    def _collect_order_book_data(self, symbol: str) -> Dict[str, Any]:
        """收集订单簿数据"""
        base_price = 50000 if "BTC" in symbol else 3000
        
        return {
            "best_bid": base_price * 0.999,
            "best_ask": base_price * 1.001,
            "bid_depth": 1000000,
            "ask_depth": 1200000,
            "spread": base_price * 0.002,
            "liquidity_score": 0.85,
        }
    
    def _collect_account_info(self) -> Dict[str, Any]:
        """收集账户信息"""
        return {
            "total_balance": 100000,
            "available_balance": 80000,
            "used_margin": 20000,
            "free_margin": 60000,
            "margin_level": 300,  # 300%
            "open_positions": 2,
            "leverage_usage": 0.2,  # 20%
        }
    
    def _collect_position_info(self, symbol: str) -> Dict[str, Any]:
        """收集持仓信息"""
        return {
            "symbol": symbol,
            "position_size": 0.5,  # 0.5 BTC
            "entry_price": 48000,
            "current_price": 50000,
            "unrealized_pnl": 1000,  # $1000 profit
            "position_type": "long",
            "leverage": 2.0,
        }
    
    def _collect_risk_metrics(self, symbol: str) -> Dict[str, Any]:
        """收集风险指标"""
        return {
            "portfolio_var": 0.03,  # 3% VaR
            "position_risk": 0.01,  # 1% position risk
            "correlation_risk": 0.02,
            "liquidity_risk": 0.005,
            "max_drawdown": 0.05,
            "sharpe_ratio": 1.5,
        }
    
    def _analyze_market_conditions(self, market_data: Dict[str, Any], order_book_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析市场条件"""
        current_price = market_data.get("current_price", 0)
        daily_change = market_data.get("24h_change", 0)
        volatility = market_data.get("volatility", 0.04)
        
        # 判断趋势
        if daily_change > 0.02:
            trend = "bullish"
        elif daily_change < -0.02:
            trend = "bearish"
        else:
            trend = "neutral"
        
        # 判断波动性
        if volatility < 0.02:
            vol_level = "low"
        elif volatility < 0.05:
            vol_level = "normal"
        else:
            vol_level = "high"
        
        return {
            "trend": trend,
            "volatility": vol_level,
            "liquidity": "good" if order_book_data.get("liquidity_score", 0) > 0.7 else "poor",
            "sentiment": "positive" if daily_change > 0 else "negative",
        }
    
    def _analyze_account_status(self, account_info: Dict[str, Any]) -> Dict[str, Any]:
        """分析账户状态"""
        available_balance = account_info.get("available_balance", 0)
        total_balance = account_info.get("total_balance", 1)
        margin_level = account_info.get("margin_level", 100)
        
        # 计算可用余额比例
        balance_ratio = available_balance / total_balance
        
        return {
            "available_balance": available_balance,
            "balance_utilization": 1 - balance_ratio,
            "margin_health": "good" if margin_level > 200 else "poor",
            "trading_capacity": "high" if balance_ratio > 0.5 else "limited",
            "current_exposure": account_info.get("leverage_usage", 0),
        }
    
    def _analyze_positions(self, position_info: Dict[str, Any]) -> Dict[str, Any]:
        """分析持仓状态"""
        if not position_info or position_info.get("position_size", 0) == 0:
            return {"status": "no_position", "risk": "none"}
        
        unrealized_pnl = position_info.get("unrealized_pnl", 0)
        entry_price = position_info.get("entry_price", 0)
        current_price = position_info.get("current_price", 0)
        
        if entry_price > 0:
            pnl_percentage = (current_price - entry_price) / entry_price
        else:
            pnl_percentage = 0
        
        return {
            "status": "open",
            "pnl": unrealized_pnl,
            "pnl_percentage": pnl_percentage,
            "risk": "high" if abs(pnl_percentage) > 0.1 else "normal",
        }
    
    def _generate_trading_signals(self, market_conditions: Dict[str, Any], 
                                account_status: Dict[str, Any], 
                                position_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成交易信号"""
        signals = []
        signal_strength = 0.0
        direction = "neutral"
        
        # 基于市场趋势的信号
        trend = market_conditions.get("trend", "neutral")
        if trend == "bullish":
            signals.append({"type": "trend", "direction": "buy", "strength": 0.7})
            signal_strength += 0.7
        elif trend == "bearish":
            signals.append({"type": "trend", "direction": "sell", "strength": 0.7})
            signal_strength -= 0.7
        
        # 基于账户状态的信号
        trading_capacity = account_status.get("trading_capacity", "limited")
        if trading_capacity == "high":
            signals.append({"type": "capacity", "direction": "neutral", "strength": 0.5})
        else:
            signals.append({"type": "capacity", "direction": "reduce", "strength": 0.3})
            signal_strength -= 0.2
        
        # 综合信号方向
        if signal_strength > 0.3:
            direction = "buy"
        elif signal_strength < -0.3:
            direction = "sell"
        else:
            direction = "hold"
        
        return {
            "technical_signals": signals,
            "overall_strength": abs(signal_strength),
            "direction": direction,
            "confidence": min(abs(signal_strength), 1.0),
        }
    
    def _make_trading_decision(self, trading_signals: Dict[str, Any], risk_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """做出交易决策"""
        direction = trading_signals.get("direction", "hold")
        signal_strength = trading_signals.get("overall_strength", 0)
        
        # 基于风险调整仓位大小
        portfolio_var = risk_metrics.get("portfolio_var", 0.02)
        risk_adjusted_size = min(self.max_position_size, self.risk_per_trade / portfolio_var)
        
        return {
            "action": direction,
            "position_size": risk_adjusted_size if direction != "hold" else 0,
            "confidence": signal_strength,
            "risk_adjusted": True,
        }
    
    def _assess_trading_risks(self, trading_decision: Dict[str, Any], risk_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """评估交易风险"""
        position_size = trading_decision.get("position_size", 0)
        portfolio_var = risk_metrics.get("portfolio_var", 0.02)
        
        # 计算交易风险
        trade_risk = position_size * portfolio_var
        
        if trade_risk < 0.01:
            risk_level = "low"
        elif trade_risk < 0.03:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        return {
            "trade_risk": trade_risk,
            "risk_level": risk_level,
            "var_impact": trade_risk / portfolio_var,
        }
    
    def _generate_trading_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成交易计划"""
        final_recommendation = analysis.get("final_recommendation", {})
        enhanced_insights = analysis.get("enhanced_insights", {})
        
        action = final_recommendation.get("action", "hold")
        position_size = final_recommendation.get("position_size", 0)
        
        if action == "hold":
            return {"action": "hold", "reason": "No trading signal"}
        
        # 从AI分析中获取增强的执行计划
        execution_plan = enhanced_insights.get("execution_plan", {})
        
        return {
            "action": action,
            "position_size": position_size,
            "entry_strategy": execution_plan.get("entry_strategy", "market_order"),
            "entry_price": final_recommendation.get("entry_price", 0),
            "stop_loss": final_recommendation.get("stop_loss", 0),
            "take_profit": final_recommendation.get("take_profit", 0),
            "execution_timeframe": execution_plan.get("timeframe", "immediate"),
            "split_orders": execution_plan.get("split_orders", False),
        }
    
    def _execute_entry_orders(self, trading_plan: Dict[str, Any], side: str) -> Dict[str, Any]:
        """执行入场订单"""
        action = trading_plan.get("action", "hold")
        position_size = trading_plan.get("position_size", 0)
        
        if action == "hold" or position_size == 0:
            return {"status": "not_executed", "reason": "No position size"}
        
        # 模拟订单执行
        order_id = f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            "status": "executed",
            "order_id": order_id,
            "side": side,
            "size": position_size,
            "price": trading_plan.get("entry_price", 50000),
            "timestamp": datetime.now().isoformat(),
        }
    
    def _execute_stop_orders(self, trading_plan: Dict[str, Any]) -> Dict[str, Any]:
        """执行止损订单"""
        stop_loss = trading_plan.get("stop_loss", 0)
        
        if stop_loss > 0:
            return {
                "status": "stop_loss_set",
                "stop_price": stop_loss,
                "order_id": f"stop_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            }
        
        return {"status": "no_stop_loss"}
    
    def _execute_take_profit_orders(self, trading_plan: Dict[str, Any]) -> Dict[str, Any]:
        """执行止盈订单"""
        take_profit = trading_plan.get("take_profit", 0)
        
        if take_profit > 0:
            return {
                "status": "take_profit_set",
                "target_price": take_profit,
                "order_id": f"tp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            }
        
        return {"status": "no_take_profit"}
    
    def _calculate_average_entry_price(self, orders: List[Dict[str, Any]]) -> float:
        """计算平均入场价格"""
        if not orders:
            return 0.0
        
        total_value = sum(order["price"] * order["size"] for order in orders)
        total_size = sum(order["size"] for order in orders)
        
        return total_value / total_size if total_size > 0 else 0.0
    
    def _update_trade_history(self, execution_result: Dict[str, Any], analysis: Dict[str, Any]) -> None:
        """更新交易历史"""
        trade_record = {
            "timestamp": datetime.now().isoformat(),
            "execution_result": execution_result,
            "analysis_summary": {
                "confidence": analysis.get("combined_confidence", 0),
                "ai_enhanced": analysis.get("analysis_type") == "ai_enhanced_trading",
                "final_action": analysis.get("final_recommendation", {}).get("action", "hold"),
            },
        }
        
        self.trade_history.append(trade_record)
        
        # 保持历史记录在合理大小
        if len(self.trade_history) > 100:
            self.trade_history = self.trade_history[-100:]
    
    def _calculate_confidence(self, trading_signals: Dict[str, Any]) -> float:
        """计算交易置信度"""
        return trading_signals.get("confidence", 0.3)
    
    def _assess_execution_readiness(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """评估执行准备情况"""
        # 检查是否有明确的交易决策
        if isinstance(analysis, dict) and "trading_decision" in analysis:
            trading_decision = analysis.get("trading_decision", {})
            action = trading_decision.get("action", "hold")
            confidence = trading_decision.get("confidence", 0)
        else:
            final_recommendation = analysis.get("final_recommendation", {})
            action = final_recommendation.get("action", "hold")
            confidence = final_recommendation.get("confidence", 0)
        
        # 基本执行条件检查
        ready = True
        reasons = []
        
        if action == "hold":
            ready = False
            reasons.append("Trading signal is hold")
        
        if confidence < 0.5:
            ready = False
            reasons.append("Confidence too low")
        
        # 检查风险限制
        trading_risks = analysis.get("trading_risks", {})
        if trading_risks.get("risk_level") == "high":
            ready = False
            reasons.append("Risk level too high")
        
        return {
            "ready": ready,
            "reason": "; ".join(reasons) if reasons else "Ready to execute",
            "confidence": confidence,
            "action": action,
        }