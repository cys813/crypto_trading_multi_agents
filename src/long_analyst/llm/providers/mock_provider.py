"""
Mock LLM Provider Implementation.

Provides a mock implementation for testing and development
without requiring actual API credentials.
"""

import asyncio
import time
import random
from typing import Dict, Any, Optional, List
import logging
import json

from .base_provider import BaseLLMProvider, LLMRequest, LLMResponse, ProviderConfig, LLMProviderType


class MockProvider(BaseLLMProvider):
    """
    Mock LLM provider for testing and development.

    Simulates LLM responses without making actual API calls.
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize mock provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self.logger.info("Mock LLM provider initialized")

        # Mock response templates
        self.response_templates = {
            "analysis": self._get_analysis_response(),
            "evaluation": self._get_evaluation_response(),
            "narrative": self._get_narrative_response(),
            "risk": self._get_risk_response(),
            "enhancement": self._get_enhancement_response(),
            "default": self._get_default_response()
        }

        # Mock model information
        self.model_info = {
            "name": "mock-model",
            "max_tokens": 4000,
            "supports_streaming": True,
            "supports_function_calling": False
        }

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate mock response.

        Args:
            request: LLM request parameters

        Returns:
            Mock LLM response
        """
        start_time = time.time()

        # Simulate API delay
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # Determine response type based on prompt content
        response_type = self._determine_response_type(request.prompt)

        # Get response template
        template = self.response_templates.get(response_type, self.response_templates["default"])

        # Customize response based on request
        content = self._customize_response(template, request)

        # Calculate metrics
        latency = time.time() - start_time
        tokens_used = len(content.split())  # Simple token estimation
        cost = 0.0  # Mock provider is free

        return LLMResponse(
            content=content,
            model=request.model or self.config.model,
            tokens_used=tokens_used,
            cost=cost,
            latency=latency,
            success=True,
            metadata={
                "mock_provider": True,
                "response_type": response_type,
                "simulated_delay": latency
            }
        )

    async def batch_generate(self, requests: List[LLMRequest]) -> List[LLMResponse]:
        """
        Generate mock responses for multiple requests.

        Args:
            requests: List of LLM requests

        Returns:
            List of mock LLM responses
        """
        # Process all requests concurrently (no rate limiting for mock)
        tasks = [self.generate(request) for request in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        results = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                self.logger.error(f"Mock batch request {i} failed: {response}")
                results.append(LLMResponse(
                    content="",
                    model=requests[i].model or self.config.model,
                    tokens_used=0,
                    cost=0.0,
                    latency=0.0,
                    success=False,
                    error_message=f"Mock processing error: {response}"
                ))
            else:
                results.append(response)

        return results

    async def health_check(self) -> bool:
        """
        Mock health check.

        Returns:
            Always True for mock provider
        """
        return True

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get mock model information.

        Returns:
            Mock model information
        """
        return {
            "provider": "mock",
            "available_models": ["mock-model", "mock-gpt-4", "mock-claude"],
            "default_model": self.config.model,
            "costs_per_1k_tokens": {"mock-model": 0.0},
            "max_tokens": 4000,
            "supports_streaming": True,
            "supports_function_calling": False,
            "mock_provider": True
        }

    def _determine_response_type(self, prompt: str) -> str:
        """Determine response type based on prompt content."""
        prompt_lower = prompt.lower()

        if "analysis" in prompt_lower or "technical" in prompt_lower:
            return "analysis"
        elif "evaluation" in prompt_lower or "signal" in prompt_lower:
            return "evaluation"
        elif "narrative" in prompt_lower or "story" in prompt_lower:
            return "narrative"
        elif "risk" in prompt_lower or "assessment" in prompt_lower:
            return "risk"
        elif "enhancement" in prompt_lower or "improve" in prompt_lower:
            return "enhancement"
        else:
            return "default"

    def _customize_response(self, template: str, request: LLMRequest) -> str:
        """Customize response template based on request."""
        # Extract key information from prompt
        if "bitcoin" in request.prompt.lower() or "btc" in request.prompt.lower():
            symbol = "BTC"
            price = 45000
        elif "ethereum" in request.prompt.lower() or "eth" in request.prompt.lower():
            symbol = "ETH"
            price = 2500
        else:
            symbol = "CRYPTO"
            price = 1000

        # Replace placeholders
        response = template.replace("{symbol}", symbol)
        response = response.replace("{price}", str(price))
        response = response.replace("{model}", request.model or self.config.model)

        # Add temperature-based variation
        if request.temperature > 0.7:
            response += "\n\n[Note: Higher temperature setting may increase creativity but decrease consistency]"
        elif request.temperature < 0.3:
            response += "\n\n[Note: Lower temperature setting increases consistency but may reduce creativity]"

        return response

    def _get_analysis_response(self) -> str:
        """Get mock analysis response template."""
        return """Based on the technical analysis of {symbol} at ${price}, here is the comprehensive assessment:

**Market Context:**
{symbol} is currently in a consolidation phase with mixed signals across different timeframes. The daily chart shows a descending triangle pattern, while the 4-hour timeframe indicates bullish divergence forming.

**Technical Analysis:**
- RSI (14): 52.3 - Neutral territory, neither overbought nor oversold
- MACD: Bullish crossover detected on 4-hour timeframe
- Moving Averages: Price trading above 50-day MA but below 200-day MA
- Volume: Below average, suggesting lack of conviction
- Support Level: ${price * 0.95:.0f}
- Resistance Level: ${price * 1.05:.0f}

**Fundamental Analysis:**
- Network activity shows moderate growth
- On-chain metrics indicate healthy accumulation
- Development activity remains strong
- Market sentiment is cautiously optimistic

**Risk Factors:**
- Overall market volatility remains elevated
- Regulatory uncertainty persists
- Technical breakdown risk below key support

**Opportunity Assessment:**
Current risk-reward ratio is approximately 1:2.5, which is favorable for long positions. However, confirmation of breakout above resistance is recommended before entering.

**Recommendation:**
Wait for confirmation of upward momentum before establishing long positions. Consider scaling in gradually if bullish signals strengthen.

Confidence Level: 65%
Risk Level: Medium
Time Horizon: Medium-term (2-8 weeks)"""

    def _get_evaluation_response(self) -> str:
        """Get mock evaluation response template."""
        return """Signal Quality Evaluation:

**Overall Assessment:**
Quality Score: 0.78/1.0
Confidence: 75%
Risk Level: Medium

**Signal Strengths:**
- Multiple technical indicators align (RSI, MACD, Volume)
- Strong support level nearby
- Favorable risk-reward ratio
- Confirms broader market trend

**Signal Weaknesses:**
- Volume confirmation is lacking
- Overhead resistance nearby
- Potential false breakout risk
- Market volatility elevated

**Market Conditions:**
Current market conditions are moderately favorable for this signal. The overall trend is bullish, but there are resistance levels that could impede progress.

**Risk-Reward Analysis:**
- Potential Reward: 12-15%
- Potential Risk: 4-5%
- Risk-Reward Ratio: 1:3 (favorable)

**Recommendations:**
1. Wait for volume confirmation before entry
2. Consider partial position sizing to manage risk
3. Set stop-loss below key support level
4. Take profit at resistance levels incrementally

**Optimal Timeframe:**
This signal is most relevant for medium-term trading (1-4 weeks). Short-term traders should be more cautious due to volatility."""

    def _get_narrative_response(self) -> str:
        """Get mock narrative response template."""
        return """The Market Story: {symbol}'s Current Chapter

{symbol} finds itself at a critical juncture, trading in a tight range as market participants weigh competing narratives. The cryptocurrency, currently valued at ${price}, is caught between bulls who see it as undervalued given improving fundamentals and bears who point to technical resistance and macroeconomic headwinds.

**Setting the Scene:**
The market is characterized by cautious optimism. Recent price action suggests a battle between accumulation and distribution, with smart money quietly building positions while retail traders remain on the sidelines. Trading volumes have been modest, indicating that the market is waiting for a catalyst.

**The Plot Thickens:**
Technical indicators paint a nuanced picture. On one hand, we're seeing signs of bottoming patterns and bullish divergences on lower timeframes. On the other hand, the broader trend remains in question, with {symbol} struggling to overcome key resistance levels that have capped previous rallies.

**Key Developments:**
Several factors are influencing the current narrative:
- Improving on-chain metrics suggest organic adoption
- Development activity continues at a steady pace
- Institutional interest appears to be growing
- Regulatory clarity is slowly improving
- Market sentiment is shifting from fear to cautious optimism

**Looking Ahead:**
The coming weeks could be decisive. If {symbol} can break above the psychological ${price * 1.05:.0f} level with strong volume, it could trigger a new wave of buying interest. Conversely, failure to hold support at ${price * 0.95:.0f} could lead to a retest of lower levels.

**The Bottom Line:**
{symbol} is at a "prove it" moment. The technical setup suggests potential, but the market needs to see sustained buying pressure to confirm the bullish thesis. Patience and risk management remain key virtues in this environment."""

    def _get_risk_response(self) -> str:
        """Get mock risk assessment response template."""
        return """Comprehensive Risk Assessment for {symbol} Position:

**Overall Risk Level: MEDIUM-HIGH (7.2/10)**

**Risk Breakdown:**

1. **Market Risk: 8/10**
   - High volatility environment (30-day volatility: 45%)
   - Correlation risk with broader crypto market
   - Liquidity risk during extreme market moves
   - Potential for rapid price swings

2. **Technical Risk: 6/10**
   - Approaching key resistance level
   - Bearish divergence on some indicators
   - Volume confirmation lacking
   - Risk of false breakout

3. **Fundamental Risk: 5/10**
   - Regulatory uncertainty remains
   - Competition in the space increasing
   - Development progress steady but not exceptional
   - Adoption metrics showing moderate growth

4. **Operational Risk: 3/10**
   - Exchange risk (low for major exchanges)
   - Custody risk manageable with proper security
   - Technical infrastructure robust
   - Counterparty risk minimal

**Key Risk Factors:**
1. **Market Sentiment Shift:** Rapid changes in market sentiment could trigger stop-losses
2. **Regulatory News:** Unexpected regulatory announcements could cause volatility
3. **Technical Failure:** Failure to break resistance could lead to sharp pullback
4. **Liquidity Crisis:** Reduced liquidity during stress events could exacerbate moves

**Mitigation Strategies:**
1. **Position Sizing:** Limit exposure to 2-3% of portfolio
2. **Stop-Loss:** Place stop-loss at ${price * 0.92:.0f}
3. **Take Profit:** Scale out at ${price * 1.08:.0f} and ${price * 1.15:.0f}
4. **Hedging:** Consider inverse ETFs or options for partial hedge
5. **Monitoring:** Set price alerts and monitor key indicators

**Worst-Case Scenario:**
- Maximum potential loss: 15-20%
- Probability of worst-case: 25%
- Recovery timeframe: 3-6 months

**Recommended Actions:**
1. Enter position gradually rather than all at once
2. Use tight stop-losses
3. Have clear exit strategy
4. Monitor market conditions closely
5. Be prepared to exit quickly if conditions deteriorate"""

    def _get_enhancement_response(self) -> str:
        """Get mock enhancement response template."""
        return """Enhanced Analysis Improvements:

**Original Analysis Strengths:**
- Good technical pattern recognition
- Solid risk assessment
- Clear entry/exit criteria
- Considered multiple timeframes

**Enhancements Made:**

1. **Improved Context:**
   - Added broader market context and correlation analysis
   - Incorporated recent news catalysts and events
   - Enhanced sentiment analysis with social media metrics
   - Added institutional flow data

2. **Enhanced Technical Analysis:**
   - Additional indicator analysis (Ichimoku Cloud, Elliott Wave)
   - Volume profile analysis added
   - Multiple timeframe alignment assessment
   - Advanced pattern recognition

3. **Better Risk Quantification:**
   - Added VaR (Value at Risk) calculations
   - Incorporated maximum drawdown analysis
   - Enhanced position sizing recommendations
   - Added correlation risk assessment

4. **Updated Fundamentals:**
   - Latest development progress updates
   - Recent partnership announcements
   - Updated on-chain metrics
   - Competitive landscape analysis

5. **Market Microstructure:**
   - Order flow analysis
   - Market depth assessment
   - Liquidity analysis across exchanges
   - Institutional positioning insights

**New Insights Discovered:**
- Strong institutional accumulation detected
- Unusual options activity suggesting upside potential
- On-chain metrics showing bullish divergence
- Development activity acceleration

**Quality Improvements:**
- Analysis confidence increased from 65% to 78%
- Risk assessment refined with better quantification
- Entry timing improved with volume confirmation
- Exit strategy enhanced with multiple targets

**Additional Data Needed:**
- Real-time order book depth
- Institutional positioning reports
- Regulatory development timeline
- Competitive product launches

**Confidence Improvement:**
The enhanced analysis shows increased confidence due to:
- Multiple confirming signals
- Better data quality
- Comprehensive risk assessment
- Institutional alignment

**Overall Enhancement:**
The enhanced analysis provides significantly more actionable insights with better risk management and higher confidence levels. The addition of institutional context and advanced technical analysis substantially improves decision quality."""

    def _get_default_response(self) -> str:
        """Get default mock response template."""
        return """This is a mock response from the {model} LLM provider.

The request was processed successfully with the following parameters:
- Model: {model}
- Max Tokens: {max_tokens}
- Temperature: {temperature}
- Prompt Length: {prompt_length} characters

**Mock Response Content:**
I have analyzed your request and generated this comprehensive response. As a mock provider, I simulate the behavior of real LLM services without requiring actual API credentials or incurring costs.

**Key Features:**
- Fast response times (0.1-0.5 seconds)
- No API rate limits
- No costs incurred
- Consistent response quality
- Suitable for testing and development

**Usage Notes:**
This mock provider is ideal for:
- Development and testing
- Integration validation
- Performance benchmarking
- Cost-free experimentation

For production use, replace this mock provider with actual LLM service providers like OpenAI, Anthropic, or Azure OpenAI.

**Response Details:**
- Content generated successfully
- All request parameters respected
- Formatting and structure maintained
- Error handling implemented
- Performance metrics tracked

The mock provider provides a realistic simulation of LLM services while eliminating external dependencies and costs."""