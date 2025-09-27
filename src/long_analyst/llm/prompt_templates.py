"""
Prompt Templates for LLM Analysis.

Provides specialized prompt templates for market analysis,
signal evaluation, and decision making.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import yaml

from ..models.market_data import MarketData
from ..models.signal import Signal, SignalType, SignalStrength


@dataclass
class PromptTemplate:
    """Individual prompt template with metadata."""
    name: str
    template: str
    description: str
    variables: List[str]
    version: str = "1.0"
    category: str = "general"

    def render(self, context: Dict[str, Any]) -> str:
        """Render template with context variables."""
        try:
            return self.template.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing required variable in template '{self.name}': {e}")

    def validate_context(self, context: Dict[str, Any]) -> bool:
        """Validate that all required variables are present."""
        return all(var in context for var in self.variables)


class PromptTemplates:
    """
    Management system for prompt templates.

    Loads, manages, and provides access to various prompt templates
    for LLM analysis tasks.
    """

    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize prompt templates manager.

        Args:
            templates_dir: Directory containing template files
        """
        self.logger = logging.getLogger(__name__)
        self.templates: Dict[str, PromptTemplate] = {}
        self.templates_dir = templates_dir or os.path.join(os.path.dirname(__file__), "templates")

        # Load built-in templates
        self._load_built_in_templates()

        # Load custom templates if directory exists
        if os.path.exists(self.templates_dir):
            self._load_custom_templates()

        self.logger.info(f"Prompt templates initialized: {len(self.templates)} templates loaded")

    def _load_built_in_templates(self):
        """Load built-in prompt templates."""
        # Long Analysis Template
        self.add_template(PromptTemplate(
            name="long_analysis",
            template=self._get_long_analysis_template(),
            description="Comprehensive long-position market analysis template",
            variables=["market_data", "context", "historical_context", "additional_factors"],
            category="analysis"
        ))

        # Signal Evaluation Template
        self.add_template(PromptTemplate(
            name="signal_evaluation",
            template=self._get_signal_evaluation_template(),
            description="Trading signal quality evaluation template",
            variables=["signal_details", "market_context", "risk_factors"],
            category="evaluation"
        ))

        # Market Narrative Template
        self.add_template(PromptTemplate(
            name="market_narrative",
            template=self._get_market_narrative_template(),
            description="Market narrative generation template",
            variables=["market_summary", "key_events", "sentiment_data", "technical_analysis"],
            category="narrative"
        ))

        # Risk Assessment Template
        self.add_template(PromptTemplate(
            name="risk_assessment",
            template=self._get_risk_assessment_template(),
            description="Comprehensive risk assessment template",
            variables=["position_details", "market_conditions", "risk_factors"],
            category="risk"
        ))

        # Enhancement Template
        self.add_template(PromptTemplate(
            name="analysis_enhancement",
            template=self._get_analysis_enhancement_template(),
            description="Analysis enhancement template",
            variables=["original_analysis", "new_data", "performance_metrics"],
            category="enhancement"
        ))

        # Quick Decision Template
        self.add_template(PromptTemplate(
            name="quick_decision",
            template=self._get_quick_decision_template(),
            description="Rapid decision making template",
            variables=["current_price", "signals", "time_constraint"],
            category="decision"
        ))

    def _load_custom_templates(self):
        """Load custom templates from directory."""
        try:
            template_files = Path(self.templates_dir).glob("*.yaml")
            for template_file in template_files:
                self._load_template_file(template_file)
        except Exception as e:
            self.logger.warning(f"Failed to load custom templates: {e}")

    def _load_template_file(self, file_path: Path):
        """Load template from YAML file."""
        try:
            with open(file_path, 'r') as f:
                template_data = yaml.safe_load(f)

            template = PromptTemplate(
                name=template_data["name"],
                template=template_data["template"],
                description=template_data.get("description", ""),
                variables=template_data.get("variables", []),
                version=template_data.get("version", "1.0"),
                category=template_data.get("category", "custom")
            )

            self.add_template(template)
            self.logger.info(f"Loaded custom template: {template.name}")

        except Exception as e:
            self.logger.error(f"Failed to load template from {file_path}: {e}")

    def add_template(self, template: PromptTemplate):
        """Add a template to the collection."""
        self.templates[template.name] = template

    def get_template(self, name: str) -> PromptTemplate:
        """Get template by name."""
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")
        return self.templates[name]

    def get_templates_by_category(self, category: str) -> List[PromptTemplate]:
        """Get all templates in a specific category."""
        return [t for t in self.templates.values() if t.category == category]

    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates."""
        return [
            {
                "name": template.name,
                "description": template.description,
                "category": template.category,
                "version": template.version,
                "variables": template.variables
            }
            for template in self.templates.values()
        ]

    def render_template(self, name: str, context: Dict[str, Any]) -> str:
        """Render template with context."""
        template = self.get_template(name)

        if not template.validate_context(context):
            missing_vars = [var for var in template.variables if var not in context]
            raise ValueError(f"Missing required variables for template '{name}': {missing_vars}")

        return template.render(context)

    def get_analysis_template(self) -> str:
        """Get the main analysis template."""
        return self.get_template("long_analysis").template

    def get_enhancement_template(self) -> str:
        """Get the enhancement template."""
        return self.get_template("analysis_enhancement").template

    def get_signal_evaluation_template(self) -> str:
        """Get the signal evaluation template."""
        return self.get_template("signal_evaluation").template

    def get_narrative_template(self) -> str:
        """Get the narrative template."""
        return self.get_template("market_narrative").template

    def _get_long_analysis_template(self) -> str:
        """Get comprehensive long analysis template."""
        return """You are an expert cryptocurrency long analyst with deep knowledge of technical analysis, market psychology, and risk management.

Analyze the following market data for potential long opportunities:

**MARKET DATA:**
{market_data}

**CURRENT CONTEXT:**
{context}

**HISTORICAL CONTEXT:**
{historical_context}

**ADDITIONAL FACTORS:**
{additional_factors}

Please provide a comprehensive analysis including:

1. **MARKET CONTEXT**: Current market conditions, trends, and key levels
2. **TECHNICAL ANALYSIS**: Key technical indicators, patterns, and signals
3. **FUNDAMENTAL ANALYSIS**: Project fundamentals, ecosystem health, and adoption metrics
4. **SENTIMENT ANALYSIS**: Market sentiment, social media trends, and news impact
5. **RISK ASSESSMENT**: Key risk factors and potential downside scenarios
6. **OPPORTUNITY ASSESSMENT**: Strength of long opportunity, entry points, and timing
7. **PRICE TARGETS**: Short-term, medium-term, and long-term price projections
8. **RISK MANAGEMENT**: Stop-loss levels, position sizing, and exit strategies
9. **INVESTMENT THESIS**: Overall rationale for long position with confidence level
10. **RECOMMENDATION**: Clear buy/hold/sell recommendation with reasoning

Format your response as structured JSON with the following fields:
{{
    "market_context": "Detailed market context analysis",
    "technical_patterns": ["List of technical patterns identified"],
    "key_levels": [List of key price levels],
    "risk_factors": ["List of key risk factors"],
    "opportunities": ["List of opportunity factors"],
    "investment_thesis": "Comprehensive investment thesis",
    "overall_score": 0.0-1.0 score for overall analysis,
    "technical_score": 0.0-1.0 score for technical analysis,
    "fundamental_score": 0.0-1.0 score for fundamental analysis,
    "sentiment_score": 0.0-1.0 score for sentiment analysis,
    "recommendation": "STRONG_BUY|BUY|HOLD|SELL|STRONG_SELL",
    "confidence": 0.0-1.0 confidence level,
    "time_horizon": "short_term|medium_term|long_term",
    "stop_loss": "Suggested stop-loss level",
    "take_profit": "Suggested take-profit level"
}}

Be thorough, objective, and provide specific data-driven insights."""

    def _get_signal_evaluation_template(self) -> str:
        """Get signal evaluation template."""
        return """You are an expert signal validation specialist. Evaluate the quality and reliability of the following trading signal:

**SIGNAL DETAILS:**
{signal_details}

**MARKET CONTEXT:**
{market_context}

**RISK FACTORS:**
{risk_factors}

Please evaluate this signal based on:

1. **SIGNAL QUALITY**: Technical validity, strength, and reliability
2. **MARKET CONDITIONS**: How current market conditions affect signal validity
3. **RISK-REWARD RATIO**: Potential upside vs. downside risk
4. **TIMING SUITABILITY**: Is this the right time to act on this signal?
5. **CONFOUNDING FACTORS**: Any factors that might invalidate the signal
6. **ALTERNATIVE SCENARIOS**: What could go wrong or right with this signal?

Provide your evaluation as structured JSON:
{{
    "quality_score": 0.0-1.0 score for signal quality,
    "confidence": 0.0-1.0 confidence in evaluation,
    "reasoning": "Detailed reasoning for evaluation",
    "strengths": ["List of signal strengths"],
    "weaknesses": ["List of signal weaknesses"],
    "recommendations": ["List of actionable recommendations"],
    "risk_level": "LOW|MEDIUM|HIGH",
    "expected_accuracy": "Estimated accuracy percentage",
    "optimal_timeframe": "Best timeframe for this signal"
}}

Be critical and objective in your evaluation."""

    def _get_market_narrative_template(self) -> str:
        """Get market narrative template."""
        return """You are a skilled market storyteller. Create a compelling narrative that explains the current market situation:

**MARKET SUMMARY:**
{market_summary}

**KEY EVENTS:**
{key_events}

**SENTIMENT DATA:**
{sentiment_data}

**TECHNICAL ANALYSIS:**
{technical_analysis}

Create a comprehensive market narrative that:

1. **SETS THE SCENE**: Describe the current market environment and key themes
2. **TELLS THE STORY**: Explain how we got here and what's driving the market
3. **HIGHLIGHTS KEY FACTORS**: Emphasize the most important influencing factors
4. **PROVIDES CONTEXT**: Explain how current events fit into the bigger picture
5. **OFFERS INSIGHTS**: Share unique perspectives and forward-looking analysis
6. **MAKES IT RELATABLE**: Use analogies and comparisons to make complex concepts understandable

Your narrative should be engaging, informative, and suitable for both technical and non-technical audiences. Focus on telling the story behind the numbers and helping readers understand what's really happening in the market."""

    def _get_risk_assessment_template(self) -> str:
        """Get risk assessment template."""
        return """You are a risk management specialist. Conduct a comprehensive risk assessment for the following position:

**POSITION DETAILS:**
{position_details}

**MARKET CONDITIONS:**
{market_conditions}

**RISK FACTORS:**
{risk_factors}

Assess the following risk dimensions:

1. **MARKET RISK**: Price volatility, correlation risk, liquidity risk
2. **COUNTERPARTY RISK**: Exchange risk, custody risk, regulatory risk
3. **OPERATIONAL RISK**: Technical failures, connectivity issues, human error
4. **LEVERAGE RISK**: Liquidation risk, margin call risk, funding risk
5. **REGULATORY RISK**: Legal changes, compliance issues, taxation
6. **CONCENTRATION RISK**: Overexposure to single asset or sector
7. **TIMING RISK**: Entry/exit timing risk, market timing risk
8. **BLACK SWAN RISK**: Unpredictable market events, systemic risk

Provide your risk assessment as structured JSON:
{{
    "overall_risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "risk_scores": {{
        "market_risk": 0.0-1.0,
        "counterparty_risk": 0.0-1.0,
        "operational_risk": 0.0-1.0,
        "leverage_risk": 0.0-1.0,
        "regulatory_risk": 0.0-1.0,
        "concentration_risk": 0.0-1.0,
        "timing_risk": 0.0-1.0,
        "black_swan_risk": 0.0-1.0
    }},
    "key_risk_factors": ["List of top risk factors"],
    "mitigation_strategies": ["List of risk mitigation strategies"],
    "monitoring_recommendations": ["List of monitoring recommendations"],
    "worst_case_scenario": "Description of worst-case scenario",
    "probability_of_loss": "Estimated probability of loss",
    "potential_loss_amount": "Estimated potential loss amount",
    "recommended_actions": ["List of recommended actions"]
}}

Be thorough and conservative in your risk assessment."""

    def _get_analysis_enhancement_template(self) -> str:
        """Get analysis enhancement template."""
        return """You are an expert analyst specializing in improving existing analysis. Enhance the following analysis:

**ORIGINAL ANALYSIS:**
{original_analysis}

**NEW DATA:**
{new_data}

**PERFORMANCE METRICS:**
{performance_metrics}

Improve the analysis by:

1. **VALIDATION**: Verify the original analysis with new data
2. **CORRECTION**: Identify and correct any errors or omissions
3. **ENHANCEMENT**: Add new insights and perspectives
4. **CONTEXT**: Provide additional context and background
5. **QUANTIFICATION**: Add more specific numbers and metrics
6. **TIMELINESS**: Ensure analysis reflects current market conditions
7. **COMPLETENESS**: Fill in missing pieces of the analysis
8. **CLARITY**: Make the analysis clearer and more actionable

Provide enhanced analysis as structured JSON:
{{
    "enhanced_analysis": "Complete enhanced analysis",
    "improvements_made": ["List of specific improvements"],
    "new_insights": ["List of new insights"],
    "corrections": ["List of corrections made"],
    "confidence_improvement": "How much confidence improved",
    "quality_score": 0.0-1.0 score for enhanced analysis,
    "actionability": "How actionable the enhanced analysis is",
    "additional_data_needed": ["List of additional data that would be helpful"]
}}

Focus on making the analysis more accurate, complete, and useful for decision-making."""

    def _get_quick_decision_template(self) -> str:
        """Get quick decision template."""
        return """You need to make a rapid trading decision. Analyze the following information and provide a clear recommendation:

**CURRENT PRICE:** ${current_price}

**SIGNALS:**
{signals}

**TIME CONSTRAINT:** {time_constraint}

Consider:
- Signal strength and reliability
- Current price action
- Risk-reward ratio
- Time constraints
- Market conditions

Provide a quick but well-reasoned decision:

{{
    "decision": "BUY|SELL|HOLD",
    "confidence": 0.0-1.0,
    "reasoning": "Brief but clear reasoning",
    "urgency": "LOW|MEDIUM|HIGH",
    "key_factors": ["Top 2-3 factors driving decision"],
    "immediate_action": "What to do right now"
}}

Be decisive and focus on the most critical factors."""

    def save_template(self, template: PromptTemplate, file_path: str):
        """Save template to file."""
        template_data = {
            "name": template.name,
            "template": template.template,
            "description": template.description,
            "variables": template.variables,
            "version": template.version,
            "category": template.category
        }

        with open(file_path, 'w') as f:
            yaml.dump(template_data, f, default_flow_style=False)

        self.logger.info(f"Template '{template.name}' saved to {file_path}")

    def optimize_prompt_length(self, template_name: str, context: Dict[str, Any], max_tokens: int) -> str:
        """Optimize prompt length to fit token limits."""
        template = self.get_template(template_name)

        # Start with full context
        full_prompt = template.render(context)

        # Estimate tokens (rough approximation)
        estimated_tokens = len(full_prompt.split()) * 1.3

        if estimated_tokens <= max_tokens:
            return full_prompt

        # If too long, reduce context strategically
        optimized_context = self._optimize_context_for_tokens(context, max_tokens)
        return template.render(optimized_context)

    def _optimize_context_for_tokens(self, context: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
        """Optimize context to fit token limits."""
        # Simple optimization - in production, use more sophisticated methods
        optimized = {}

        # Prioritize essential fields
        essential_fields = ["market_data", "current_price", "signals"]
        for field in essential_fields:
            if field in context:
                optimized[field] = context[field]

        # Add remaining fields if space allows
        remaining_fields = [k for k in context.keys() if k not in essential_fields]
        for field in remaining_fields[:3]:  # Limit to 3 additional fields
            optimized[field] = context[field]

        return optimized