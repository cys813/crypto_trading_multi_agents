"""
加密货币交易工作流图

基于原版TradingAgents的图结构，专门为加密货币交易优化
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..agents.analysts.technical_analyst import TechnicalAnalyst
from ..agents.analysts.onchain_analyst import OnchainAnalyst  
from ..agents.analysts.sentiment_analyst import SentimentAnalyst
from ..agents.analysts.market_maker_analyst import MarketMakerAnalyst
from ..agents.analysts.defi_analyst import DefiAnalyst
from ..agents.researchers.bull_researcher import BullResearcher
from ..agents.researchers.bear_researcher import BearResearcher
from ..agents.traders.crypto_trader import CryptoTrader
from ..agents.risk_managers.crypto_risk_manager import CryptoRiskManager
from ..agents.managers.research_manager import ResearchManager
from ..config.exchange_config import ExchangeConfig

logger = logging.getLogger(__name__)

class CryptoTradingGraph:
    """加密货币交易工作流图"""
    
    def __init__(self, config: Dict[str, Any], debug: bool = False):
        """
        初始化交易图
        
        Args:
            config: 配置字典
            debug: 是否启用调试模式
        """
        self.config = config
        self.debug = debug
        self.config_manager = ExchangeConfig()
        
        # 初始化智能体
        self._initialize_agents()
        
        # 工作流状态
        self.current_state = {}
        self.analysis_history = []
        
        logger.info("CryptoTradingGraph initialized successfully")
    
    def _initialize_agents(self):
        """初始化所有智能体"""
        # 分析师团队
        self.technical_analyst = TechnicalAnalyst(self.config)
        self.onchain_analyst = OnchainAnalyst(self.config)
        self.sentiment_analyst = SentimentAnalyst(self.config)
        self.market_maker_analyst = MarketMakerAnalyst(self.config)
        self.defi_analyst = DefiAnalyst(self.config)
        
        # 研究团队
        self.bull_researcher = BullResearcher(self.config)
        self.bear_researcher = BearResearcher(self.config)
        self.research_manager = ResearchManager(self.config)
        
        # 交易和风控
        self.crypto_trader = CryptoTrader(self.config)
        self.crypto_risk_manager = CryptoRiskManager(self.config)
    
    def propagate(self, symbol: str, end_date: str, **kwargs) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        执行完整的分析流程
        
        Args:
            symbol: 交易对符号 (如 "BTC/USDT")
            end_date: 分析截止日期
            **kwargs: 其他参数
            
        Returns:
            tuple: (状态字典, 决策字典)
        """
        try:
            # 初始化状态
            self.current_state = {
                "symbol": symbol,
                "end_date": end_date,
                "start_time": datetime.now(),
                "analysis_depth": kwargs.get("analysis_depth", "3"),
                "market_condition": kwargs.get("market_condition", "normal"),
                **kwargs
            }
            
            logger.info(f"Starting analysis for {symbol} with depth {self.current_state['analysis_depth']}")
            
            # 第一阶段：数据收集和基础分析
            self._phase1_data_collection()
            
            # 第二阶段：专业分析
            self._phase2_specialized_analysis()
            
            # 第三阶段：研究辩论
            self._phase3_research_debate()
            
            # 第四阶段：风险评估
            self._phase4_risk_assessment()
            
            # 第五阶段：交易决策
            self._phase5_trading_decision()
            
            # 完成状态
            self.current_state["end_time"] = datetime.now()
            self.current_state["duration"] = (
                self.current_state["end_time"] - self.current_state["start_time"]
            ).total_seconds()
            
            # 生成最终决策
            final_decision = self._generate_final_decision()
            
            # 记录分析历史
            self.analysis_history.append({
                "timestamp": datetime.now(),
                "symbol": symbol,
                "state": self.current_state.copy(),
                "decision": final_decision.copy()
            })
            
            logger.info(f"Analysis completed for {symbol} in {self.current_state['duration']:.2f}s")
            
            return self.current_state, final_decision
            
        except Exception as e:
            logger.error(f"Error during analysis propagation: {str(e)}")
            raise
    
    def _phase1_data_collection(self):
        """第一阶段：数据收集和基础分析"""
        if self.debug:
            logger.info("Phase 1: Data Collection and Basic Analysis")
        
        # 并行执行基础数据收集
        tasks = [
            ("technical_data", self.technical_analyst.collect_data),
            ("onchain_data", self.onchain_analyst.collect_data),
            ("sentiment_data", self.sentiment_analyst.collect_data),
            ("market_data", self.market_maker_analyst.collect_data),
        ]
        
        # 根据分析深度选择性执行
        if self.current_state["analysis_depth"] in ["4", "5"]:
            tasks.append(("defi_data", self.defi_analyst.collect_data))
        
        # 执行数据收集
        for data_type, collect_func in tasks:
            try:
                self.current_state[f"{data_type}"] = collect_func(
                    self.current_state["symbol"],
                    self.current_state["end_date"]
                )
            except Exception as e:
                logger.warning(f"Failed to collect {data_type}: {str(e)}")
                self.current_state[f"{data_type}"] = {"error": str(e)}
    
    def _phase2_specialized_analysis(self):
        """第二阶段：专业分析"""
        if self.debug:
            logger.info("Phase 2: Specialized Analysis")
        
        # 技术分析
        if "technical_data" in self.current_state:
            self.current_state["technical_analysis"] = self.technical_analyst.analyze(
                self.current_state["technical_data"]
            )
        
        # 链上分析
        if "onchain_data" in self.current_state:
            self.current_state["onchain_analysis"] = self.onchain_analyst.analyze(
                self.current_state["onchain_data"]
            )
        
        # 情绪分析
        if "sentiment_data" in self.current_state:
            self.current_state["sentiment_analysis"] = self.sentiment_analyst.analyze(
                self.current_state["sentiment_data"]
            )
        
        # 做市分析
        if "market_data" in self.current_state:
            self.current_state["market_analysis"] = self.market_maker_analyst.analyze(
                self.current_state["market_data"]
            )
        
        # DeFi分析（深度分析时执行）
        if self.current_state["analysis_depth"] in ["4", "5"] and "defi_data" in self.current_state:
            self.current_state["defi_analysis"] = self.defi_analyst.analyze(
                self.current_state["defi_data"]
            )
    
    def _phase3_research_debate(self):
        """第三阶段：研究辩论"""
        if self.debug:
            logger.info("Phase 3: Research Debate")
        
        # 准备辩论材料
        debate_material = {
            "technical_analysis": self.current_state.get("technical_analysis", {}),
            "onchain_analysis": self.current_state.get("onchain_analysis", {}),
            "sentiment_analysis": self.current_state.get("sentiment_analysis", {}),
            "market_analysis": self.current_state.get("market_analysis", {}),
            "defi_analysis": self.current_state.get("defi_analysis", {}),
        }
        
        # 看涨研究员分析
        bull_analysis = self.bull_researcher.analyze(debate_material)
        
        # 看跌研究员分析
        bear_analysis = self.bear_researcher.analyze(debate_material)
        
        # 研究经理综合辩论
        self.current_state["research_summary"] = self.research_manager.synthesize(
            bull_analysis, bear_analysis, debate_material
        )
    
    def _phase4_risk_assessment(self):
        """第四阶段：风险评估"""
        if self.debug:
            logger.info("Phase 4: Risk Assessment")
        
        risk_factors = {
            "market_risk": self.current_state.get("technical_analysis", {}).get("risk_indicators", {}),
            "liquidity_risk": self.current_state.get("market_analysis", {}).get("liquidity_metrics", {}),
            "sentiment_risk": self.current_state.get("sentiment_analysis", {}).get("risk_signals", {}),
            "onchain_risk": self.current_state.get("onchain_analysis", {}).get("risk_metrics", {}),
        }
        
        # 添加DeFi风险（如果存在）
        if "defi_analysis" in self.current_state:
            risk_factors["defi_risk"] = self.current_state["defi_analysis"].get("risk_metrics", {})
        
        self.current_state["risk_assessment"] = self.crypto_risk_manager.assess(risk_factors)
    
    def _phase5_trading_decision(self):
        """第五阶段：交易决策"""
        if self.debug:
            logger.info("Phase 5: Trading Decision")
        
        decision_inputs = {
            "symbol": self.current_state["symbol"],
            "research_summary": self.current_state.get("research_summary", {}),
            "risk_assessment": self.current_state.get("risk_assessment", {}),
            "technical_analysis": self.current_state.get("technical_analysis", {}),
            "market_condition": self.current_state.get("market_condition", "normal"),
            "analysis_depth": self.current_state["analysis_depth"],
        }
        
        self.current_state["trading_decision"] = self.crypto_trader.make_decision(decision_inputs)
    
    def _generate_final_decision(self) -> Dict[str, Any]:
        """生成最终决策"""
        trading_decision = self.current_state.get("trading_decision", {})
        risk_assessment = self.current_state.get("risk_assessment", {})
        
        return {
            "symbol": self.current_state["symbol"],
            "action": trading_decision.get("action", "HOLD"),
            "confidence": trading_decision.get("confidence", 0.5),
            "risk_score": risk_assessment.get("overall_score", 0.5),
            "position_size": trading_decision.get("position_size", 0.0),
            "entry_price": trading_decision.get("entry_price", 0.0),
            "stop_loss": trading_decision.get("stop_loss", 0.0),
            "take_profit": trading_decision.get("take_profit", 0.0),
            "time_horizon": trading_decision.get("time_horizon", "medium"),
            "reasoning": trading_decision.get("reasoning", ""),
            "key_factors": trading_decision.get("key_factors", []),
            "risk_factors": risk_assessment.get("key_risks", []),
            "analysis_timestamp": self.current_state["end_time"].isoformat(),
            "analysis_duration": self.current_state.get("duration", 0),
            "analysis_depth": self.current_state["analysis_depth"],
        }
    
    def backtest(self, symbol: str, start_date: str, end_date: str, 
                 strategy: str = "momentum", **kwargs) -> Dict[str, Any]:
        """
        策略回测
        
        Args:
            symbol: 交易对符号
            start_date: 开始日期
            end_date: 结束日期
            strategy: 策略类型
            **kwargs: 其他参数
            
        Returns:
            回测结果
        """
        # TODO: 实现回测功能
        pass
    
    def get_analysis_history(self, symbol: Optional[str] = None, 
                           limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取分析历史
        
        Args:
            symbol: 过滤的交易对
            limit: 返回数量限制
            
        Returns:
            分析历史列表
        """
        history = self.analysis_history
        
        if symbol:
            history = [h for h in history if h["symbol"] == symbol]
        
        return history[-limit:]
    
    def get_current_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.current_state.copy()