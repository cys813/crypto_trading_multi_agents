"""
代理工具函数 - 为各种代理提供通用工具函数

基于原版代理工具，针对加密货币市场特性优化
"""

from typing import Dict, Any, List, Optional, Union
import logging
import json
import time
import math
from datetime import datetime, timedelta
import re
from enum import Enum

logger = logging.getLogger(__name__)

class AnalysisLevel(Enum):
    """分析深度级别"""
    QUICK = "quick"          # 快速分析 (2-3分钟)
    BASIC = "basic"          # 基础分析 (3-5分钟)
    STANDARD = "standard"    # 标准分析 (5-8分钟)
    DEEP = "deep"           # 深度分析 (8-12分钟)
    COMPREHENSIVE = "comprehensive"  # 综合分析 (12-20分钟)

class TimeHorizon(Enum):
    """时间周期"""
    SHORT_TERM = "short_term"      # 短期 (1-7天)
    MEDIUM_TERM = "medium_term"    # 中期 (1-4周)
    LONG_TERM = "long_term"        # 长期 (1-6个月)
    VERY_LONG_TERM = "very_long_term"  # 超长期 (6个月以上)

class RiskLevel(Enum):
    """风险级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class AgentUtils:
    """代理工具类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化代理工具
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.analysis_config = config.get("analysis_config", {})
        self.risk_config = config.get("risk_config", {})
        
    def estimate_analysis_time(self, analysis_level: AnalysisLevel, 
                             data_complexity: str = "medium") -> int:
        """
        估算分析时间
        
        Args:
            analysis_level: 分析级别
            data_complexity: 数据复杂度 (low, medium, high)
            
        Returns:
            估算时间（秒）
        """
        base_times = {
            AnalysisLevel.QUICK: 180,         # 3分钟
            AnalysisLevel.BASIC: 300,         # 5分钟
            AnalysisLevel.STANDARD: 480,      # 8分钟
            AnalysisLevel.DEEP: 720,          # 12分钟
            AnalysisLevel.COMPREHENSIVE: 1200 # 20分钟
        }
        
        complexity_multiplier = {
            "low": 0.8,
            "medium": 1.0,
            "high": 1.3
        }
        
        base_time = base_times.get(analysis_level, 300)
        multiplier = complexity_multiplier.get(data_complexity, 1.0)
        
        return int(base_time * multiplier)
    
    def calculate_confidence_score(self, signal_strength: float, 
                                 data_quality: float, 
                                 model_accuracy: float = 0.8) -> float:
        """
        计算置信度分数
        
        Args:
            signal_strength: 信号强度 (0-1)
            data_quality: 数据质量 (0-1)
            model_accuracy: 模型准确率 (0-1)
            
        Returns:
            置信度分数 (0-1)
        """
        weights = self.analysis_config.get("confidence_weights", {
            "signal_strength": 0.4,
            "data_quality": 0.4,
            "model_accuracy": 0.2
        })
        
        confidence = (
            weights["signal_strength"] * signal_strength +
            weights["data_quality"] * data_quality +
            weights["model_accuracy"] * model_accuracy
        )
        
        return max(0.0, min(1.0, confidence))
    
    def assess_data_quality(self, data_completeness: float, 
                           data_freshness: float, 
                           data_accuracy: float) -> float:
        """
        评估数据质量
        
        Args:
            data_completeness: 数据完整性 (0-1)
            data_freshness: 数据新鲜度 (0-1)
            data_accuracy: 数据准确性 (0-1)
            
        Returns:
            数据质量分数 (0-1)
        """
        weights = self.analysis_config.get("data_quality_weights", {
            "completeness": 0.3,
            "freshness": 0.4,
            "accuracy": 0.3
        })
        
        quality_score = (
            weights["completeness"] * data_completeness +
            weights["freshness"] * data_freshness +
            weights["accuracy"] * data_accuracy
        )
        
        return max(0.0, min(1.0, quality_score))
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        标准化交易对符号
        
        Args:
            symbol: 原始符号
            
        Returns:
            标准化符号
        """
        # 移除空格
        symbol = symbol.strip().upper()
        
        # 标准化分隔符
        symbol = symbol.replace('-', '/').replace('_', '/')
        
        # 确保格式为 BASE/QUOTE
        if '/' not in symbol:
            # 常见币种默认配对
            if symbol in ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'DOT']:
                symbol += '/USDT'
            else:
                symbol += '/USDT'
        
        return symbol
    
    def extract_base_currency(self, symbol: str) -> str:
        """
        提取基础货币
        
        Args:
            symbol: 交易对符号
            
        Returns:
            基础货币
        """
        normalized = self.normalize_symbol(symbol)
        return normalized.split('/')[0]
    
    def extract_quote_currency(self, symbol: str) -> str:
        """
        提取报价货币
        
        Args:
            symbol: 交易对符号
            
        Returns:
            报价货币
        """
        normalized = self.normalize_symbol(symbol)
        return normalized.split('/')[1]
    
    def calculate_position_size(self, account_balance: float, 
                               risk_per_trade: float, 
                               stop_loss_percentage: float,
                               current_price: float) -> float:
        """
        计算仓位大小
        
        Args:
            account_balance: 账户余额
            risk_per_trade: 每笔交易风险比例 (0-1)
            stop_loss_percentage: 止损百分比 (0-1)
            current_price: 当前价格
            
        Returns:
            仓位大小
        """
        risk_amount = account_balance * risk_per_trade
        position_size = risk_amount / (current_price * stop_loss_percentage)
        
        # 应用最大仓位限制
        max_position_ratio = self.risk_config.get("max_position_ratio", 0.2)
        max_position = account_balance * max_position_ratio / current_price
        
        return min(position_size, max_position)
    
    def calculate_risk_reward_ratio(self, entry_price: float, 
                                   stop_loss: float, 
                                   take_profit: float) -> float:
        """
        计算风险回报比
        
        Args:
            entry_price: 入场价格
            stop_loss: 止损价格
            take_profit: 止盈价格
            
        Returns:
            风险回报比
        """
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        return reward / risk if risk > 0 else 0.0
    
    def assess_market_volatility(self, price_data: List[Dict[str, Any]], 
                               period: int = 24) -> Dict[str, Any]:
        """
        评估市场波动性
        
        Args:
            price_data: 价格数据
            period: 周期（小时）
            
        Returns:
            波动性评估结果
        """
        if len(price_data) < 2:
            return {"error": "Insufficient price data"}
        
        # 计算价格变化
        prices = [item.get("close", 0) for item in price_data[-period:]]
        
        if len(prices) < 2:
            return {"error": "Insufficient price data for period"}
        
        # 计算对数收益率
        log_returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0 and prices[i] > 0:
                log_return = math.log(prices[i] / prices[i-1])
                log_returns.append(log_return)
        
        if not log_returns:
            return {"error": "Invalid price data"}
        
        # 计算波动率
        import statistics
        volatility = statistics.stdev(log_returns) * math.sqrt(24 * 365)  # 年化波动率
        
        # 波动性分类
        if volatility < 0.5:
            volatility_level = "low"
        elif volatility < 1.0:
            volatility_level = "medium"
        elif volatility < 2.0:
            volatility_level = "high"
        else:
            volatility_level = "extreme"
        
        return {
            "volatility": volatility,
            "volatility_level": volatility_level,
            "period_hours": period,
            "data_points": len(prices),
        }
    
    def detect_market_regime(self, market_data: Dict[str, Any]) -> str:
        """
        检测市场制度
        
        Args:
            market_data: 市场数据
            
        Returns:
            市场制度 (bullish, bearish, sideways, volatile)
        """
        trend = market_data.get("trend", "unknown")
        volatility = market_data.get("volatility_level", "medium")
        
        if trend == "bullish" and volatility in ["low", "medium"]:
            return "bullish"
        elif trend == "bearish" and volatility in ["low", "medium"]:
            return "bearish"
        elif volatility == "extreme":
            return "volatile"
        else:
            return "sideways"
    
    def format_crypto_amount(self, amount: float, currency: str) -> str:
        """
        格式化加密货币数量
        
        Args:
            amount: 数量
            currency: 货币符号
            
        Returns:
            格式化字符串
        """
        if currency == "BTC":
            return f"{amount:.8f} BTC"
        elif currency == "ETH":
            return f"{amount:.6f} ETH"
        elif currency == "USDT":
            return f"${amount:.2f}"
        else:
            return f"{amount:.4f} {currency}"
    
    def calculate_portfolio_metrics(self, positions: List[Dict[str, Any]], 
                                  current_prices: Dict[str, float]) -> Dict[str, Any]:
        """
        计算投资组合指标
        
        Args:
            positions: 持仓列表
            current_prices: 当前价格字典
            
        Returns:
            投资组合指标
        """
        total_value = 0.0
        total_cost = 0.0
        position_values = {}
        
        for position in positions:
            symbol = position.get("symbol")
            amount = position.get("amount", 0)
            cost_basis = position.get("cost_basis", 0)
            
            if symbol and symbol in current_prices:
                current_price = current_prices[symbol]
                position_value = amount * current_price
                position_cost = amount * cost_basis
                
                total_value += position_value
                total_cost += position_cost
                
                position_values[symbol] = {
                    "value": position_value,
                    "cost": position_cost,
                    "pnl": position_value - position_cost,
                    "pnl_percentage": ((position_value - position_cost) / position_cost * 100) if position_cost > 0 else 0
                }
        
        total_pnl = total_value - total_cost
        total_pnl_percentage = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "total_value": total_value,
            "total_cost": total_cost,
            "total_pnl": total_pnl,
            "total_pnl_percentage": total_pnl_percentage,
            "positions": position_values,
        }
    
    def generate_trading_signals(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成交易信号
        
        Args:
            analysis_results: 分析结果
            
        Returns:
            交易信号列表
        """
        signals = []
        
        # 基于技术分析生成信号
        if "technical_analysis" in analysis_results:
            tech_signals = self._generate_technical_signals(analysis_results["technical_analysis"])
            signals.extend(tech_signals)
        
        # 基于情绪分析生成信号
        if "sentiment_analysis" in analysis_results:
            sentiment_signals = self._generate_sentiment_signals(analysis_results["sentiment_analysis"])
            signals.extend(sentiment_signals)
        
        # 基于链上分析生成信号
        if "onchain_analysis" in analysis_results:
            onchain_signals = self._generate_onchain_signals(analysis_results["onchain_analysis"])
            signals.extend(onchain_signals)
        
        return signals
    
    def _generate_technical_signals(self, tech_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成技术分析信号"""
        signals = []
        
        # RSI信号
        rsi = tech_analysis.get("rsi", 50)
        if rsi < 30:
            signals.append({
                "type": "buy",
                "indicator": "RSI",
                "strength": "strong",
                "reason": f"RSI ({rsi}) indicates oversold conditions"
            })
        elif rsi > 70:
            signals.append({
                "type": "sell",
                "indicator": "RSI",
                "strength": "strong",
                "reason": f"RSI ({rsi}) indicates overbought conditions"
            })
        
        # MACD信号
        macd_signal = tech_analysis.get("macd_signal", "neutral")
        if macd_signal == "bullish":
            signals.append({
                "type": "buy",
                "indicator": "MACD",
                "strength": "moderate",
                "reason": "MACD shows bullish crossover"
            })
        elif macd_signal == "bearish":
            signals.append({
                "type": "sell",
                "indicator": "MACD",
                "strength": "moderate",
                "reason": "MACD shows bearish crossover"
            })
        
        return signals
    
    def _generate_sentiment_signals(self, sentiment_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成情绪分析信号"""
        signals = []
        
        fgi = sentiment_analysis.get("fear_greed_index", 50)
        if fgi < 25:
            signals.append({
                "type": "buy",
                "indicator": "Fear & Greed Index",
                "strength": "strong",
                "reason": f"Extreme fear (FGI: {fgi}) - potential buying opportunity"
            })
        elif fgi > 75:
            signals.append({
                "type": "sell",
                "indicator": "Fear & Greed Index",
                "strength": "strong",
                "reason": f"Extreme greed (FGI: {fgi}) - potential correction risk"
            })
        
        return signals
    
    def _generate_onchain_signals(self, onchain_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成链上分析信号"""
        signals = []
        
        # 鲸鱼活动信号
        whale_activity = onchain_analysis.get("whale_activity", "normal")
        if whale_activity == "accumulation":
            signals.append({
                "type": "buy",
                "indicator": "On-chain",
                "strength": "moderate",
                "reason": "Whale accumulation detected"
            })
        elif whale_activity == "distribution":
            signals.append({
                "type": "sell",
                "indicator": "On-chain",
                "strength": "moderate",
                "reason": "Whale distribution detected"
            })
        
        return signals
    
    def validate_analysis_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证分析参数
        
        Args:
            params: 分析参数
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        # 验证必需参数
        required_params = ["symbol", "analysis_level"]
        for param in required_params:
            if param not in params:
                errors.append(f"Missing required parameter: {param}")
        
        # 验证符号格式
        if "symbol" in params:
            symbol = params["symbol"]
            if not self._validate_symbol_format(symbol):
                errors.append(f"Invalid symbol format: {symbol}")
        
        # 验证分析级别
        if "analysis_level" in params:
            level = params["analysis_level"]
            if not isinstance(level, str) or level not in [l.value for l in AnalysisLevel]:
                errors.append(f"Invalid analysis level: {level}")
        
        # 验证风险参数
        if "risk_tolerance" in params:
            risk = params["risk_tolerance"]
            if risk not in [r.value for r in RiskLevel]:
                warnings.append(f"Unusual risk tolerance: {risk}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "normalized_params": self._normalize_parameters(params)
        }
    
    def _validate_symbol_format(self, symbol: str) -> bool:
        """验证符号格式"""
        pattern = r'^[A-Z0-9]{2,10}/[A-Z0-9]{2,10}$'
        return bool(re.match(pattern, self.normalize_symbol(symbol)))
    
    def _normalize_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """标准化参数"""
        normalized = params.copy()
        
        # 标准化符号
        if "symbol" in normalized:
            normalized["symbol"] = self.normalize_symbol(normalized["symbol"])
        
        # 确保分析级别为枚举值
        if "analysis_level" in normalized:
            level = normalized["analysis_level"]
            if isinstance(level, str):
                for enum_level in AnalysisLevel:
                    if enum_level.value == level:
                        normalized["analysis_level"] = enum_level
                        break
        
        return normalized
    
    def create_analysis_report(self, results: Dict[str, Any], 
                              symbol: str, 
                              analysis_level: AnalysisLevel) -> Dict[str, Any]:
        """
        创建分析报告
        
        Args:
            results: 分析结果
            symbol: 交易对
            analysis_level: 分析级别
            
        Returns:
            分析报告
        """
        return {
            "symbol": symbol,
            "analysis_level": analysis_level.value,
            "timestamp": datetime.now().isoformat(),
            "summary": self._generate_summary(results),
            "key_findings": self._extract_key_findings(results),
            "recommendations": self._generate_recommendations(results),
            "risk_assessment": self._assess_risks(results),
            "confidence": self._calculate_overall_confidence(results),
            "data_sources": self._list_data_sources(results),
            "execution_time": results.get("execution_time", 0),
        }
    
    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """生成分析摘要"""
        # 简化的摘要生成逻辑
        decision = results.get("trading_decision", {}).get("trading_decision", "hold")
        confidence = results.get("trading_decision", {}).get("confidence", 0.5)
        
        if decision == "buy":
            return f"分析建议买入，置信度 {confidence:.1%}"
        elif decision == "sell":
            return f"分析建议卖出，置信度 {confidence:.1%}"
        else:
            return f"分析建议观望，置信度 {confidence:.1%}"
    
    def _extract_key_findings(self, results: Dict[str, Any]) -> List[str]:
        """提取关键发现"""
        findings = []
        
        # 从各个分析中提取关键发现
        if "market_trend" in results:
            trend = results["market_trend"].get("primary_trend", "unknown")
            findings.append(f"市场趋势: {trend}")
        
        if "sentiment_analysis" in results:
            sentiment = results["sentiment_analysis"].get("overall_sentiment", "unknown")
            findings.append(f"市场情绪: {sentiment}")
        
        return findings
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        decision = results.get("trading_decision", {}).get("trading_decision", "hold")
        if decision == "buy":
            recommendations.append("建议逐步建仓")
            recommendations.append("设置止损保护")
        elif decision == "sell":
            recommendations.append("建议减仓避险")
            recommendations.append("锁定部分利润")
        else:
            recommendations.append("建议观望等待")
            recommendations.append("关注市场变化")
        
        return recommendations
    
    def _assess_risks(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """评估风险"""
        return {
            "overall_risk": "medium",
            "key_risks": ["市场波动性", "监管不确定性"],
            "risk_mitigation": ["分散投资", "设置止损"]
        }
    
    def _calculate_overall_confidence(self, results: Dict[str, Any]) -> float:
        """计算总体置信度"""
        # 简化的置信度计算
        confidence_scores = []
        
        if "trading_decision" in results:
            confidence_scores.append(results["trading_decision"].get("confidence", 0.5))
        
        if "research_debate" in results:
            confidence_scores.append(results["research_debate"].get("confidence", 0.5))
        
        if "risk_debate" in results:
            confidence_scores.append(results["risk_debate"].get("confidence", 0.5))
        
        return sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
    
    def _list_data_sources(self, results: Dict[str, Any]) -> List[str]:
        """列出数据源"""
        sources = []
        
        # 基于分析内容推断数据源
        if "market_trend" in results:
            sources.append("技术分析数据")
        
        if "sentiment_analysis" in results:
            sources.append("情绪数据")
        
        if "onchain_analysis" in results:
            sources.append("链上数据")
        
        return sources