"""
做市商分析师 - 专注加密货币市场微观结构分析

基于原版分析架构，针对市场流动性和订单簿分析优化
"""

from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta

from ..services.ai_analysis_mixin import StandardAIAnalysisMixin

logger = logging.getLogger(__name__)

class MarketMakerAnalyst(StandardAIAnalysisMixin):
    """加密货币做市商分析师"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化做市商分析师
        
        Args:
            config: 配置字典
        """
        super().__init__()
        self.config = config
        self.supported_exchanges = config.get("crypto_config", {}).get("supported_exchanges", [])
        
        # 初始化统一LLM服务
        from ..services.llm_service import initialize_llm_service
        from ..config.ai_analysis_config import get_unified_llm_service_config
        
        llm_config = get_unified_llm_service_config()
        initialize_llm_service(llm_config)
        
        # 市场微观结构指标权重
        self.microstructure_weights = {
            "order_book_imbalance": 0.25,
            "liquidity_depth": 0.20,
            "spread_analysis": 0.20,
            "volume_profile": 0.15,
            "market_impact": 0.20,
        }
    
    def collect_data(self, symbol: str, end_date: str) -> Dict[str, Any]:
        """
        收集市场微观结构数据
        
        Args:
            symbol: 交易对符号
            end_date: 截止日期
            
        Returns:
            市场微观结构数据
        """
        try:
            # TODO: 实现真实的市场微观结构数据收集逻辑
            # 这里使用模拟数据
            
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            start_dt = end_dt - timedelta(days=1)  # 做市分析通常用短期数据
            
            return {
                "symbol": symbol,
                "start_date": start_dt.strftime("%Y-%m-%d"),
                "end_date": end_date,
                "order_book_data": self._generate_order_book_data(symbol),
                "tick_data": self._generate_tick_data(symbol),
                "volume_profile": self._generate_volume_profile(symbol),
                "liquidity_metrics": self._generate_liquidity_metrics(symbol),
                "market_impact_data": self._generate_market_impact_data(symbol),
            }
            
        except Exception as e:
            logger.error(f"Error collecting market maker data for {symbol}: {str(e)}")
            return {"error": str(e)}
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析市场微观结构数据 - AI增强版本
        
        Args:
            data: 市场微观结构数据
            
        Returns:
            市场微观结构分析结果（包含AI增强分析）
        """
        try:
            if "error" in data:
                return {"error": data["error"]}
            
            # 执行传统分析
            traditional_analysis = self._perform_traditional_analysis(data)
            
            # 使用AI增强分析
            return self.analyze_with_ai_enhancement(
                data, 
                lambda raw_data: traditional_analysis
            )
            
        except Exception as e:
            logger.error(f"Error analyzing market maker data: {str(e)}")
            return {"error": str(e)}
    
    def _perform_traditional_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行传统的市场微观结构分析
        
        Args:
            data: 市场微观结构数据
            
        Returns:
            传统分析结果
        """
        order_book_data = data.get("order_book_data", {})
        tick_data = data.get("tick_data", {})
        volume_profile = data.get("volume_profile", {})
        liquidity_metrics = data.get("liquidity_metrics", {})
        market_impact_data = data.get("market_impact_data", {})
        
        # 分析订单簿
        order_book_analysis = self._analyze_order_book(order_book_data)
        
        # 分析流动性
        liquidity_analysis = self._analyze_liquidity(liquidity_metrics)
        
        # 分析价差
        spread_analysis = self._analyze_spreads(order_book_data, tick_data)
        
        # 分析成交量分布
        volume_analysis = self._analyze_volume_profile(volume_profile)
        
        # 分析市场冲击
        market_impact_analysis = self._analyze_market_impact(market_impact_data)
        
        # 检测异常交易模式
        anomaly_detection = self._detect_trading_anomalies(tick_data, order_book_data)
        
        # 风险评估
        risk_metrics = self._assess_market_risk(
            order_book_analysis, liquidity_analysis, market_impact_analysis
        )
        
        # 生成做市信号
        market_signals = self._generate_market_signals(
            order_book_analysis, liquidity_analysis, spread_analysis
        )
        
        return {
            "order_book_analysis": order_book_analysis,
            "liquidity_analysis": liquidity_analysis,
            "spread_analysis": spread_analysis,
            "volume_analysis": volume_analysis,
            "market_impact_analysis": market_impact_analysis,
            "anomaly_detection": anomaly_detection,
            "risk_metrics": risk_metrics,
            "market_signals": market_signals,
            "confidence": self._calculate_confidence(market_signals),
            "key_observations": self._generate_key_observations(
                order_book_analysis, liquidity_analysis, spread_analysis
            ),
        }
    
    def _build_market_maker_analysis_prompt(self, raw_data: Dict[str, Any], traditional_analysis: Dict[str, Any]) -> str:
        """
        构建市场微观结构分析的AI提示词
        
        Args:
            raw_data: 原始数据
            traditional_analysis: 传统分析结果
            
        Returns:
            AI分析提示词
        """
        symbol = raw_data.get("symbol", "Unknown")
        
        # 订单簿分析摘要
        order_book_summary = traditional_analysis.get("order_book_analysis", {})
        order_book_pressure = order_book_summary.get("pressure", "balanced")
        order_book_imbalance = order_book_summary.get("imbalance", 0.0)
        
        # 流动性分析摘要
        liquidity_summary = traditional_analysis.get("liquidity_analysis", {})
        liquidity_quality = liquidity_summary.get("quality", "unknown")
        liquidity_score = liquidity_summary.get("overall_score", 0.5)
        
        # 价差分析摘要
        spread_summary = traditional_analysis.get("spread_analysis", {})
        spread_level = spread_summary.get("spread_level", "normal")
        
        # 市场信号摘要
        market_signals = traditional_analysis.get("market_signals", {})
        bullish_signals = len(market_signals.get("bullish_signals", []))
        bearish_signals = len(market_signals.get("bearish_signals", []))
        
        prompt = f"""
作为专业的加密货币市场微观结构分析师，请基于以下传统分析结果提供深度AI增强分析：

## 交易对信息
- 符号: {symbol}
- 分析时间: {raw_data.get('end_date', 'Unknown')}

## 传统分析结果摘要

### 订单簿分析
- 买卖压力: {order_book_pressure}  
- 不平衡度: {order_book_imbalance:.3f}
- 深度健康度: {order_book_summary.get('order_book_health', 'unknown')}

### 流动性分析
- 流动性质量: {liquidity_quality}
- 流动性评分: {liquidity_score:.3f}
- 深度充足性: {liquidity_summary.get('depth_sufficiency', 'unknown')}

### 价差分析
- 价差水平: {spread_level}
- 名义价差: {spread_summary.get('spread_percentage', 0):.4f}%
- 有效价差: {spread_summary.get('effective_spread', 0):.4f}%

### 市场信号
- 看涨信号数量: {bullish_signals}
- 看跌信号数量: {bearish_signals}

## 请提供以下AI增强分析

### 1. 做市策略建议
- 基于当前市场微观结构，推荐最适合的做市策略
- 分析买卖价差设置的最优区间
- 评估流动性提供的风险回报比

### 2. 异常模式识别
- 识别可能的市场操纵行为
- 检测大额订单对市场结构的影响
- 分析交易模式的异常特征

### 3. 风险评估与预警
- 评估当前市场结构的脆弱性
- 预测可能的流动性枯竭风险
- 识别潜在的市场震荡因素

### 4. 机会识别
- 识别价差套利机会
- 分析流动性不平衡带来的获利机会
- 评估短期交易策略的可行性

### 5. 综合建议
- 基于AI分析的最终交易建议 (买入/卖出/观望)
- 建议的持仓规模和时间框架
- 风险控制要点

请以JSON格式返回分析结果，确保包含具体的数值和可执行的建议。
"""
        return prompt
    
    def _combine_market_maker_analyses(self, traditional_analysis: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        整合传统分析和AI分析结果
        
        Args:
            traditional_analysis: 传统分析结果
            ai_analysis: AI分析结果
            
        Returns:
            整合后的分析结果
        """
        # 整合置信度
        traditional_confidence = traditional_analysis.get("confidence", 0.3)
        ai_confidence = ai_analysis.get("confidence", 0.3)
        combined_confidence = (traditional_confidence * 0.4 + ai_confidence * 0.6)
        
        # 整合交易建议
        traditional_signals = traditional_analysis.get("market_signals", {})
        ai_recommendation = ai_analysis.get("trading_recommendation", {})
        
        combined_recommendation = {
            "action": ai_recommendation.get("action", "hold"),
            "confidence": combined_confidence,
            "traditional_bias": self._get_signal_bias(traditional_signals),
            "ai_bias": ai_recommendation.get("action", "hold"),
            "consensus": self._determine_consensus(traditional_signals, ai_recommendation),
        }
        
        # 创建增强洞察
        enhanced_insights = {
            "market_structure_health": ai_analysis.get("market_structure_health", "unknown"),
            "liquidity_outlook": ai_analysis.get("liquidity_outlook", "stable"),
            "volatility_forecast": ai_analysis.get("volatility_forecast", "normal"),
            "trading_opportunities": ai_analysis.get("trading_opportunities", []),
            "risk_factors": ai_analysis.get("risk_factors", []),
            "optimal_strategy": ai_analysis.get("optimal_strategy", "market_making"),
        }
        
        return {
            **traditional_analysis,
            "ai_analysis": ai_analysis,
            "combined_confidence": combined_confidence,
            "final_recommendation": combined_recommendation,
            "enhanced_insights": enhanced_insights,
            "analysis_type": "ai_enhanced_market_maker",
        }
    
    def _get_signal_bias(self, signals: Dict[str, Any]) -> str:
        """从传统信号中提取偏向"""
        bullish_count = len(signals.get("bullish_signals", []))
        bearish_count = len(signals.get("bearish_signals", []))
        
        if bullish_count > bearish_count:
            return "bullish"
        elif bearish_count > bullish_count:
            return "bearish"
        else:
            return "neutral"
    
    def _determine_consensus(self, traditional_signals: Dict[str, Any], ai_recommendation: Dict[str, Any]) -> str:
        """确定传统分析和AI分析的共识"""
        traditional_bias = self._get_signal_bias(traditional_signals)
        ai_bias = ai_recommendation.get("action", "hold")
        
        # 映射AI动作到偏向
        ai_bias_mapping = {"buy": "bullish", "sell": "bearish", "hold": "neutral"}
        ai_bias_normalized = ai_bias_mapping.get(ai_bias, "neutral")
        
        if traditional_bias == ai_bias_normalized:
            return f"strong_{traditional_bias}"
        else:
            return "mixed"

    def _generate_order_book_data(self, symbol: str) -> Dict[str, Any]:
        """生成订单簿数据"""
        base_price = 50000 if "BTC" in symbol else 3000
        
        # 生成订单簿深度
        bids = []
        asks = []
        
        for i in range(10):
            bid_price = base_price * (1 - 0.001 * (i + 1))
            ask_price = base_price * (1 + 0.001 * (i + 1))
            
            bids.append({
                "price": bid_price,
                "quantity": base_price * 0.1 * (1 - i * 0.05),  # 递减数量
                "total": sum(bid["quantity"] for bid in bids[:i]) + base_price * 0.1 * (1 - i * 0.05),
            })
            
            asks.append({
                "price": ask_price,
                "quantity": base_price * 0.1 * (1 - i * 0.05),
                "total": sum(ask["quantity"] for ask in asks[:i]) + base_price * 0.1 * (1 - i * 0.05),
            })
        
        return {
            "bids": bids,
            "asks": asks,
            "spread": asks[0]["price"] - bids[0]["price"],
            "spread_percentage": (asks[0]["price"] - bids[0]["price"]) / base_price,
            "total_bid_depth": sum(bid["quantity"] for bid in bids),
            "total_ask_depth": sum(ask["quantity"] for ask in asks),
            "mid_price": (bids[0]["price"] + asks[0]["price"]) / 2,
            "weighted_mid_price": self._calculate_weighted_mid_price(bids, asks),
        }
    
    def _calculate_weighted_mid_price(self, bids: List[Dict], asks: List[Dict]) -> float:
        """计算加权中间价"""
        if not bids or not asks:
            return 0.0
        
        # 简化的加权中间价计算
        best_bid = bids[0]["price"]
        best_ask = asks[0]["price"]
        bid_quantity = bids[0]["quantity"]
        ask_quantity = asks[0]["quantity"]
        
        if bid_quantity + ask_quantity == 0:
            return (best_bid + best_ask) / 2
        
        return (best_bid * ask_quantity + best_ask * bid_quantity) / (bid_quantity + ask_quantity)
    
    def _generate_tick_data(self, symbol: str) -> Dict[str, Any]:
        """生成逐笔交易数据"""
        base_price = 50000 if "BTC" in symbol else 3000
        
        trades = []
        current_time = datetime.now()
        
        for i in range(100):
            # 模拟交易价格和数量
            price_change = (hash(str(i)) % 100 - 50) / 10000
            price = base_price * (1 + price_change)
            quantity = base_price * 0.01 * (hash(str(i + 1000)) % 50 + 10) / 1000
            
            trades.append({
                "timestamp": (current_time - timedelta(minutes=i)).isoformat(),
                "price": price,
                "quantity": quantity,
                "side": "buy" if hash(str(i)) % 2 == 0 else "sell",
                "trade_id": i + 1,
            })
        
        return {
            "trades": trades,
            "total_volume": sum(trade["quantity"] for trade in trades),
            "buy_volume": sum(trade["quantity"] for trade in trades if trade["side"] == "buy"),
            "sell_volume": sum(trade["quantity"] for trade in trades if trade["side"] == "sell"),
            "trade_count": len(trades),
            "average_trade_size": sum(trade["quantity"] for trade in trades) / len(trades),
        }
    
    def _generate_volume_profile(self, symbol: str) -> Dict[str, Any]:
        """生成成交量分布"""
        base_price = 50000 if "BTC" in symbol else 3000
        
        price_levels = []
        for i in range(20):
            price_level = base_price * (1 + (i - 10) * 0.01)
            volume = base_price * 0.05 * (1 - abs(i - 10) * 0.08)  # 中间价格成交量更高
            
            price_levels.append({
                "price": price_level,
                "volume": volume,
                "buy_volume": volume * 0.6,
                "sell_volume": volume * 0.4,
                "trade_count": int(volume / (base_price * 0.001)),
            })
        
        return {
            "price_levels": price_levels,
            "point_of_control": price_levels[10]["price"],  # POC - 最大成交量价格
            "value_area": {
                "high": price_levels[15]["price"],
                "low": price_levels[5]["price"],
                "volume_percentage": 0.68,  # 标准差范围
            },
            "volume_distribution": "normal",  # 正态分布
        }
    
    def _generate_liquidity_metrics(self, symbol: str) -> Dict[str, Any]:
        """生成流动性指标"""
        base_price = 50000 if "BTC" in symbol else 3000
        
        return {
            "bid_depth_1": {
                "depth": base_price * 0.5,
                "quality": "high",
            },
            "bid_depth_5": {
                "depth": base_price * 2.5,
                "quality": "high",
            },
            "ask_depth_1": {
                "depth": base_price * 0.6,
                "quality": "high",
            },
            "ask_depth_5": {
                "depth": base_price * 3.0,
                "quality": "high",
            },
            "slippage_1m": {
                "buy_slippage": 0.002,  # 0.2%
                "sell_slippage": 0.0018,
            },
            "slippage_5m": {
                "buy_slippage": 0.008,  # 0.8%
                "sell_slippage": 0.007,
            },
            "liquidity_score": 0.85,
            "market_depth_quality": "excellent",
        }
    
    def _generate_market_impact_data(self, symbol: str) -> Dict[str, Any]:
        """生成市场冲击数据"""
        base_price = 50000 if "BTC" in symbol else 3000
        
        return {
            "impact_curve": [
                {"size": base_price * 0.1, "impact": 0.001},
                {"size": base_price * 0.5, "impact": 0.003},
                {"size": base_price * 1.0, "impact": 0.006},
                {"size": base_price * 2.0, "impact": 0.012},
                {"size": base_price * 5.0, "impact": 0.025},
            ],
            "market_impact_coefficient": 0.0002,
            "permanent_impact_ratio": 0.6,
            "temporary_impact_ratio": 0.4,
            "impact_decay_time": 15,  # 分钟
        }
    
    def _analyze_order_book(self, order_book_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析订单簿"""
        bids = order_book_data.get("bids", [])
        asks = order_book_data.get("asks", [])
        
        if not bids or not asks:
            return {"imbalance": 0.0, "pressure": "neutral"}
        
        # 计算订单簿不平衡
        bid_depth = sum(bid["quantity"] for bid in bids[:5])
        ask_depth = sum(ask["quantity"] for ask in asks[:5])
        
        if bid_depth + ask_depth > 0:
            imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth)
        else:
            imbalance = 0.0
        
        # 判断压力方向
        if imbalance > 0.1:
            pressure = "buying_pressure"
        elif imbalance < -0.1:
            pressure = "selling_pressure"
        else:
            pressure = "balanced"
        
        return {
            "imbalance": imbalance,
            "pressure": pressure,
            "bid_ask_ratio": bid_depth / ask_depth if ask_depth > 0 else 1.0,
            "depth_concentration": self._calculate_depth_concentration(bids, asks),
            "order_book_health": "healthy" if abs(imbalance) < 0.3 else "imbalanced",
        }
    
    def _calculate_depth_concentration(self, bids: List[Dict], asks: List[Dict]) -> float:
        """计算深度集中度"""
        if not bids or not asks:
            return 0.0
        
        # 计算前3档深度占总深度的比例
        top_3_bid_depth = sum(bid["quantity"] for bid in bids[:3])
        top_3_ask_depth = sum(ask["quantity"] for ask in asks[:3])
        total_bid_depth = sum(bid["quantity"] for bid in bids)
        total_ask_depth = sum(ask["quantity"] for ask in asks)
        
        if total_bid_depth + total_ask_depth == 0:
            return 0.0
        
        concentration = (top_3_bid_depth + top_3_ask_depth) / (total_bid_depth + total_ask_depth)
        
        return concentration
    
    def _analyze_liquidity(self, liquidity_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """分析流动性"""
        liquidity_score = liquidity_metrics.get("liquidity_score", 0.5)
        
        # 分析不同规模的滑点
        slippage_1m = liquidity_metrics.get("slippage_1m", {})
        slippage_5m = liquidity_metrics.get("slippage_5m", {})
        
        avg_slippage_1m = (slippage_1m.get("buy_slippage", 0) + slippage_1m.get("sell_slippage", 0)) / 2
        avg_slippage_5m = (slippage_5m.get("buy_slippage", 0) + slippage_5m.get("sell_slippage", 0)) / 2
        
        # 评估流动性质量
        if liquidity_score > 0.8 and avg_slippage_1m < 0.003:
            quality = "excellent"
        elif liquidity_score > 0.6 and avg_slippage_1m < 0.005:
            quality = "good"
        elif liquidity_score > 0.4 and avg_slippage_1m < 0.01:
            quality = "fair"
        else:
            quality = "poor"
        
        return {
            "overall_score": liquidity_score,
            "quality": quality,
            "slippage_1m": avg_slippage_1m,
            "slippage_5m": avg_slippage_5m,
            "depth_sufficiency": "sufficient" if liquidity_score > 0.6 else "insufficient",
            "liquidity_trend": "stable",  # 需要历史数据计算趋势
        }
    
    def _analyze_spreads(self, order_book_data: Dict[str, Any], tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析价差"""
        spread = order_book_data.get("spread", 0)
        spread_percentage = order_book_data.get("spread_percentage", 0)
        mid_price = order_book_data.get("mid_price", 0)
        
        # 评估价差水平
        if spread_percentage < 0.001:
            spread_level = "tight"
        elif spread_percentage < 0.003:
            spread_level = "normal"
        elif spread_percentage < 0.005:
            spread_level = "wide"
        else:
            spread_level = "very_wide"
        
        # 计算有效价差（基于实际交易）
        trades = tick_data.get("trades", [])
        if trades:
            # 计算交易价格相对于中间价的偏差
            price_deviations = []
            for trade in trades[-20:]:  # 最近20笔交易
                deviation = abs(trade["price"] - mid_price) / mid_price
                price_deviations.append(deviation)
            
            effective_spread = sum(price_deviations) / len(price_deviations) if price_deviations else 0
        else:
            effective_spread = spread_percentage
        
        return {
            "nominal_spread": spread,
            "spread_percentage": spread_percentage,
            "spread_level": spread_level,
            "effective_spread": effective_spread,
            "spread_volatility": "low" if spread_percentage < 0.002 else "medium" if spread_percentage < 0.004 else "high",
        }
    
    def _analyze_volume_profile(self, volume_profile: Dict[str, Any]) -> Dict[str, Any]:
        """分析成交量分布"""
        price_levels = volume_profile.get("price_levels", [])
        poc = volume_profile.get("point_of_control", 0)
        value_area = volume_profile.get("value_area", {})
        
        # 计算成交量分布形态
        if not price_levels:
            return {"distribution": "unknown", "trend": "unknown"}
        
        # 简单的分布形态分析
        volumes = [level["volume"] for level in price_levels]
        max_volume_idx = volumes.index(max(volumes))
        
        if max_volume_idx < len(price_levels) // 3:
            distribution_type = "skewed_down"
        elif max_volume_idx > 2 * len(price_levels) // 3:
            distribution_type = "skewed_up"
        else:
            distribution_type = "normal"
        
        # 分析趋势
        poc_relative_position = max_volume_idx / len(price_levels)
        if poc_relative_position > 0.6:
            trend = "bullish"
        elif poc_relative_position < 0.4:
            trend = "bearish"
        else:
            trend = "neutral"
        
        return {
            "distribution": distribution_type,
            "trend": trend,
            "poc_price": poc,
            "value_area_high": value_area.get("high", 0),
            "value_area_low": value_area.get("low", 0),
            "volume_concentration": max(volumes) / sum(volumes) if sum(volumes) > 0 else 0,
        }
    
    def _analyze_market_impact(self, market_impact_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析市场冲击"""
        impact_curve = market_impact_data.get("impact_curve", [])
        coefficient = market_impact_data.get("market_impact_coefficient", 0)
        
        if not impact_curve:
            return {"impact_cost": "low", "market_efficiency": "high"}
        
        # 计算不同规模下的冲击成本
        avg_impact = sum(point["impact"] for point in impact_curve) / len(impact_curve)
        
        # 评估冲击成本
        if avg_impact < 0.005:
            impact_cost = "low"
        elif avg_impact < 0.015:
            impact_cost = "medium"
        else:
            impact_cost = "high"
        
        # 评估市场效率
        if coefficient < 0.0001:
            efficiency = "high"
        elif coefficient < 0.0003:
            efficiency = "medium"
        else:
            efficiency = "low"
        
        return {
            "impact_cost": impact_cost,
            "market_efficiency": efficiency,
            "average_impact": avg_impact,
            "impact_coefficient": coefficient,
            "decay_time": market_impact_data.get("impact_decay_time", 0),
        }
    
    def _detect_trading_anomalies(self, tick_data: Dict[str, Any], 
                                order_book_data: Dict[str, Any]) -> Dict[str, Any]:
        """检测交易异常"""
        anomalies = []
        anomaly_score = 0.0
        
        trades = tick_data.get("trades", [])
        if not trades:
            return {"anomalies": [], "anomaly_score": 0.0}
        
        # 检测异常大额交易
        trade_sizes = [trade["quantity"] for trade in trades]
        avg_size = sum(trade_sizes) / len(trade_sizes)
        
        for trade in trades:
            if trade["quantity"] > avg_size * 5:  # 超过平均5倍
                anomalies.append({
                    "type": "large_trade",
                    "size": trade["quantity"],
                    "timestamp": trade["timestamp"],
                    "severity": "high" if trade["quantity"] > avg_size * 10 else "medium",
                })
                anomaly_score += 0.3
        
        # 检测价格跳跃
        prices = [trade["price"] for trade in trades]
        for i in range(1, len(prices)):
            price_change = abs(prices[i] - prices[i-1]) / prices[i-1]
            if price_change > 0.005:  # 0.5%以上的价格跳跃
                anomalies.append({
                    "type": "price_jump",
                    "change": price_change,
                    "timestamp": trades[i]["timestamp"],
                    "severity": "high" if price_change > 0.01 else "medium",
                })
                anomaly_score += 0.2
        
        return {
            "anomalies": anomalies,
            "anomaly_score": min(anomaly_score, 1.0),
            "anomaly_level": "high" if anomaly_score > 0.5 else "medium" if anomaly_score > 0.2 else "low",
        }
    
    def _assess_market_risk(self, order_book_analysis: Dict[str, Any],
                           liquidity_analysis: Dict[str, Any],
                           market_impact_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """评估市场风险"""
        risk_score = 0.0
        risk_factors = []
        
        # 订单簿不平衡风险
        imbalance = order_book_analysis.get("imbalance", 0.0)
        if abs(imbalance) > 0.3:
            risk_score += 0.2
            risk_factors.append("订单簿严重不平衡")
        
        # 流动性风险
        liquidity_score = liquidity_analysis.get("overall_score", 0.5)
        if liquidity_score < 0.4:
            risk_score += 0.3
            risk_factors.append("流动性不足")
        
        # 市场冲击风险
        impact_cost = market_impact_analysis.get("impact_cost", "low")
        if impact_cost == "high":
            risk_score += 0.2
            risk_factors.append("市场冲击成本高")
        
        return {
            "overall_score": min(risk_score, 1.0),
            "risk_level": "high" if risk_score > 0.5 else "medium" if risk_score > 0.2 else "low",
            "key_risks": risk_factors,
        }
    
    def _generate_market_signals(self, order_book_analysis: Dict[str, Any],
                                liquidity_analysis: Dict[str, Any],
                                spread_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成市场信号"""
        signals = {
            "bullish_signals": [],
            "bearish_signals": [],
            "neutral_signals": [],
        }
        
        # 基于订单簿压力
        pressure = order_book_analysis.get("pressure", "neutral")
        if pressure == "buying_pressure":
            signals["bullish_signals"].append("买盘压力较大")
        elif pressure == "selling_pressure":
            signals["bearish_signals"].append("卖盘压力较大")
        
        # 基于流动性
        liquidity_quality = liquidity_analysis.get("quality", "unknown")
        if liquidity_quality == "excellent":
            signals["bullish_signals"].append("流动性充裕")
        elif liquidity_quality == "poor":
            signals["bearish_signals"].append("流动性紧张")
        
        # 基于价差
        spread_level = spread_analysis.get("spread_level", "unknown")
        if spread_level == "tight":
            signals["bullish_signals"].append("价差收窄")
        elif spread_level == "very_wide":
            signals["bearish_signals"].append("价差扩大")
        
        return signals
    
    def _calculate_confidence(self, market_signals: Dict[str, Any]) -> float:
        """计算分析置信度"""
        total_signals = len(market_signals["bullish_signals"]) + len(market_signals["bearish_signals"])
        
        if total_signals == 0:
            return 0.3
        
        # 基于信号一致性
        signal_consistency = abs(len(market_signals["bullish_signals"]) - len(market_signals["bearish_signals"])) / total_signals
        
        return signal_consistency
    
    def _generate_key_observations(self, order_book_analysis: Dict[str, Any],
                                  liquidity_analysis: Dict[str, Any],
                                  spread_analysis: Dict[str, Any]) -> List[str]:
        """生成关键观察"""
        observations = []
        
        # 订单簿观察
        pressure = order_book_analysis.get("pressure", "unknown")
        observations.append(f"订单簿压力: {pressure}")
        
        # 流动性观察
        liquidity_quality = liquidity_analysis.get("quality", "unknown")
        observations.append(f"流动性质量: {liquidity_quality}")
        
        # 价差观察
        spread_level = spread_analysis.get("spread_level", "unknown")
        observations.append(f"价差水平: {spread_level}")
        
        return observations