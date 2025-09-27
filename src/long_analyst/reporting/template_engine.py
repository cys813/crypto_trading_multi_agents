"""
Template engine for report generation
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
import yaml

from .models import TemplateConfig, ReportFormat


class TemplateEngine:
    """Template engine for report generation"""

    def __init__(self, template_dir: str = None):
        """
        Initialize template engine

        Args:
            template_dir: Directory containing template files
        """
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(__file__), "templates")

        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(exist_ok=True)

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Add custom filters
        self.env.filters['format_currency'] = self._format_currency
        self.env.filters['format_percentage'] = self._format_percentage
        self.env.filters['format_datetime'] = self._format_datetime

        # Load template configurations
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, TemplateConfig]:
        """Load template configurations"""
        templates = {}

        # Load default templates
        default_templates = {
            "standard": self._create_standard_template_config(),
            "quick_decision": self._create_quick_decision_template_config(),
            "technical": self._create_technical_template_config(),
            "comprehensive": self._create_comprehensive_template_config()
        }

        templates.update(default_templates)

        # Load custom templates from files
        config_file = self.template_dir / "templates.yaml"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                custom_configs = yaml.safe_load(f)
                for name, config_data in custom_configs.items():
                    templates[name] = TemplateConfig(**config_data)

        return templates

    def _create_standard_template_config(self) -> TemplateConfig:
        """Create standard template configuration"""
        return TemplateConfig(
            name="standard",
            description="Standard comprehensive analysis report",
            template_path="standard.html.j2",
            variables=[
                "symbol", "generated_time", "model_version",
                "technical_analysis", "fundamental_analysis", "sentiment_analysis",
                "strategy_recommendation", "risk_reward_analysis", "summary"
            ],
            output_formats=[ReportFormat.HTML, ReportFormat.PDF, ReportFormat.MARKDOWN],
            version="1.0"
        )

    def _create_quick_decision_template_config(self) -> TemplateConfig:
        """Create quick decision template configuration"""
        return TemplateConfig(
            name="quick_decision",
            description="Quick decision report for fast trading",
            template_path="quick_decision.html.j2",
            variables=[
                "symbol", "signal_strength", "recommendation", "expected_win_rate",
                "entry_price", "stop_loss_price", "take_profit_price", "risk_reward_ratio",
                "key_reasons", "key_risks"
            ],
            output_formats=[ReportFormat.HTML, ReportFormat.JSON],
            version="1.0"
        )

    def _create_technical_template_config(self) -> TemplateConfig:
        """Create technical analysis template configuration"""
        return TemplateConfig(
            name="technical",
            description="Technical analysis focused report",
            template_path="technical.html.j2",
            variables=[
                "symbol", "trend_analysis", "key_indicators", "support_resistance",
                "momentum_analysis", "volume_analysis", "pattern_recognition"
            ],
            output_formats=[ReportFormat.HTML, ReportFormat.PDF],
            version="1.0"
        )

    def _create_comprehensive_template_config(self) -> TemplateConfig:
        """Create comprehensive template configuration"""
        return TemplateConfig(
            name="comprehensive",
            description="Comprehensive multi-faceted analysis report",
            template_path="comprehensive.html.j2",
            variables=[
                "symbol", "generated_time", "model_version",
                "technical_analysis", "fundamental_analysis", "sentiment_analysis",
                "market_conditions", "risk_assessment", "strategy_recommendation",
                "historical_performance", "future_projections"
            ],
            output_formats=[ReportFormat.HTML, ReportFormat.PDF, ReportFormat.MARKDOWN],
            version="1.0"
        )

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with given context

        Args:
            template_name: Name of the template
            context: Template context data

        Returns:
            Rendered template content
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")

        template_config = self.templates[template_name]

        try:
            # Load template from file or create default
            template_path = self.template_dir / template_config.template_path
            if template_path.exists():
                template = self.env.get_template(template_config.template_path)
            else:
                template = self._create_default_template(template_name)

            # Render template
            return template.render(**context)

        except Exception as e:
            raise RuntimeError(f"Error rendering template '{template_name}': {e}")

    def _create_default_template(self, template_name: str) -> Template:
        """Create default template based on name"""
        if template_name == "standard":
            template_content = self._get_standard_template_content()
        elif template_name == "quick_decision":
            template_content = self._get_quick_decision_template_content()
        elif template_name == "technical":
            template_content = self._get_technical_template_content()
        elif template_name == "comprehensive":
            template_content = self._get_comprehensive_template_content()
        else:
            template_content = self._get_generic_template_content()

        return Template(template_content)

    def _get_standard_template_content(self) -> str:
        """Get standard template content"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>做多分析报告 - {{ symbol }}</title>
    <style>
        body { font-family: 'Arial', sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .recommendation { background-color: #e8f5e8; padding: 10px; border-radius: 3px; }
        .risk { background-color: #ffe8e8; padding: 10px; border-radius: 3px; }
        .metric { display: inline-block; margin: 5px; padding: 5px; background-color: #f9f9f9; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>做多分析报告 - {{ symbol }}</h1>
        <p>生成时间: {{ generated_time | format_datetime }}</p>
        <p>分析模型版本: {{ model_version }}</p>
    </div>

    {% if summary %}
    <div class="section">
        <h2>执行摘要</h2>
        <p><strong>信号强度:</strong> {{ summary.signal_strength.overall_score }}/10</p>
        <p><strong>置信度:</strong> {{ summary.confidence_score }}%</p>

        <h3>主要发现</h3>
        <ul>
        {% for finding in summary.key_findings %}
            <li>{{ finding }}</li>
        {% endfor %}
        </ul>

        <h3>主要建议</h3>
        <ul>
        {% for rec in summary.main_recommendations %}
            <li>{{ rec }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}

    {% if technical_analysis %}
    <div class="section">
        <h2>技术面分析</h2>
        <h3>趋势分析</h3>
        <p>{{ technical_analysis.trend }}</p>

        <h3>关键指标</h3>
        {% for indicator in technical_analysis.key_indicators %}
        <div class="metric">
            <strong>{{ indicator.name }}:</strong> {{ indicator.value }}
            <span style="color: {% if indicator.signal == 'BUY' %}green{% elif indicator.signal == 'SELL' %}red{% else %}gray{% endif %}">
                ({{ indicator.signal }})
            </span>
        </div>
        {% endfor %}

        <h3>支撑阻力位</h3>
        <p><strong>支撑位:</strong> {{ technical_analysis.support_levels | join(', ') }}</p>
        <p><strong>阻力位:</strong> {{ technical_analysis.resistance_levels | join(', ') }}</p>
    </div>
    {% endif %}

    {% if fundamental_analysis %}
    <div class="section">
        <h2>基本面分析</h2>
        <div class="metric"><strong>市值:</strong> ${{ fundamental_analysis.market_cap | format_currency }}</div>
        <div class="metric"><strong>24h成交量:</strong> ${{ fundamental_analysis.volume_24h | format_currency }}</div>
        <div class="metric"><strong>24h涨跌:</strong> {{ fundamental_analysis.price_change_24h | format_percentage }}</div>
        <div class="metric"><strong>市场占有率:</strong> {{ fundamental_analysis.market_dominance | format_percentage }}</div>
    </div>
    {% endif %}

    {% if sentiment_analysis %}
    <div class="section">
        <h2>市场情绪分析</h2>
        <p><strong>整体情绪:</strong> {{ sentiment_analysis.overall_sentiment }}</p>
        <p><strong>新闻情绪:</strong> {{ sentiment_analysis.news_sentiment | format_percentage }}</p>
        <p><strong>社交媒体情绪:</strong> {{ sentiment_analysis.social_sentiment | format_percentage }}</p>
        <p><strong>市场情绪:</strong> {{ sentiment_analysis.market_sentiment | format_percentage }}</p>
        <p><strong>置信度:</strong> {{ sentiment_analysis.confidence | format_percentage }}</p>
    </div>
    {% endif %}

    {% if strategy_recommendation %}
    <div class="section recommendation">
        <h2>策略建议</h2>
        <h3>操作建议: {{ strategy_recommendation.action }}</h3>

        <h4>入场建议</h4>
        <p><strong>建议价格:</strong> ${{ strategy_recommendation.entry_recommendation.price }}</p>
        <p><strong>入场时机:</strong> {{ strategy_recommendation.entry_recommendation.timing }}</p>
        <p><strong>置信度:</strong> {{ strategy_recommendation.entry_recommendation.confidence }}</p>

        <h4>风险管理</h4>
        <p><strong>止损价格:</strong> ${{ strategy_recommendation.risk_management.stop_loss }}</p>
        <p><strong>止盈目标:</strong> {{ strategy_recommendation.risk_management.take_profit_levels | join(', ') }}</p>
        <p><strong>建议仓位:</strong> {{ strategy_recommendation.risk_management.position_size | format_percentage }}</p>
        <p><strong>风险收益比:</strong> {{ strategy_recommendation.risk_management.risk_reward_ratio }}</p>

        <h4>主要理由</h4>
        <ul>
        {% for reason in strategy_recommendation.reasoning %}
            <li>{{ reason }}</li>
        {% endfor %}
        </ul>

        <p><strong>预期胜率:</strong> {{ strategy_recommendation.expected_win_rate | format_percentage }}</p>
        <p><strong>时间周期:</strong> {{ strategy_recommendation.time_horizon }}</p>
    </div>
    {% endif %}

    {% if risk_reward_analysis %}
    <div class="section risk">
        <h2>风险收益分析</h2>
        <div class="metric"><strong>预期收益:</strong> {{ risk_reward_analysis.expected_return | format_percentage }}</div>
        <div class="metric"><strong>最大回撤:</strong> {{ risk_reward_analysis.max_drawdown | format_percentage }}</div>
        <div class="metric"><strong>夏普比率:</strong> {{ risk_reward_analysis.sharpe_ratio }}</div>
        <div class="metric"><strong>胜率概率:</strong> {{ risk_reward_analysis.win_probability | format_percentage }}</div>
        <div class="metric"><strong>风险收益比:</strong> {{ risk_reward_analysis.risk_reward_ratio }}</div>
    </div>
    {% endif %}

    <div class="section">
        <h2>免责声明</h2>
        <p>本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
    </div>
</body>
</html>
        """.strip()

    def _get_quick_decision_template_content(self) -> str:
        """Get quick decision template content"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>快速做多决策 - {{ symbol }}</title>
    <style>
        body { font-family: 'Arial', sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 15px; border-radius: 5px; text-align: center; }
        .decision { font-size: 24px; font-weight: bold; margin: 20px 0; text-align: center; }
        .buy { color: green; }
        .hold { color: orange; }
        .sell { color: red; }
        .metrics { display: flex; justify-content: space-around; margin: 20px 0; }
        .metric { text-align: center; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }
        .reasons { margin: 20px 0; }
        .reasons h3 { color: #333; }
        .reasons ul { list-style-type: none; padding: 0; }
        .reasons li { margin: 5px 0; padding: 5px; background-color: #f0f0f0; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>快速做多决策 - {{ symbol }}</h1>
        <p>生成时间: {{ generated_time | format_datetime }}</p>
    </div>

    <div class="decision {{ recommendation.lower() }}">
        推荐操作: {{ recommendation }}
    </div>

    <div class="metrics">
        <div class="metric">
            <h3>信号强度</h3>
            <div style="font-size: 36px; font-weight: bold;">{{ signal_strength }}/10</div>
        </div>
        <div class="metric">
            <h3>预期胜率</h3>
            <div style="font-size: 36px; font-weight: bold;">{{ expected_win_rate | format_percentage }}</div>
        </div>
        <div class="metric">
            <h3>风险收益比</h3>
            <div style="font-size: 36px; font-weight: bold;">{{ risk_reward_ratio }}</div>
        </div>
    </div>

    <div class="metrics">
        <div class="metric">
            <h3>入场价格</h3>
            <div style="font-size: 24px; font-weight: bold;">${{ entry_price }}</div>
        </div>
        <div class="metric">
            <h3>止损价格</h3>
            <div style="font-size: 24px; font-weight: bold; color: red;">${{ stop_loss_price }}</div>
        </div>
        <div class="metric">
            <h3>止盈价格</h3>
            <div style="font-size: 24px; font-weight: bold; color: green;">${{ take_profit_price }}</div>
        </div>
    </div>

    <div class="reasons">
        <h3>主要理由</h3>
        <ul>
        {% for reason in key_reasons %}
            <li>{{ reason }}</li>
        {% endfor %}
        </ul>
    </div>

    <div class="reasons">
        <h3>主要风险</h3>
        <ul>
        {% for risk in key_risks %}
            <li>{{ risk }}</li>
        {% endfor %}
        </ul>
    </div>

    <div style="text-align: center; margin-top: 30px; color: #666;">
        <p>快速决策报告 - 仅供参考</p>
    </div>
</body>
</html>
        """.strip()

    def _get_technical_template_content(self) -> str:
        """Get technical analysis template content"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>技术分析报告 - {{ symbol }}</title>
    <style>
        body { font-family: 'Arial', sans-serif; margin: 20px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .indicator { display: inline-block; margin: 5px; padding: 8px; background-color: #f9f9f9; border-radius: 5px; }
        .buy { color: green; }
        .sell { color: red; }
        .neutral { color: gray; }
    </style>
</head>
<body>
    <h1>技术分析报告 - {{ symbol }}</h1>
    <p>生成时间: {{ generated_time | format_datetime }}</p>

    <div class="section">
        <h2>趋势分析</h2>
        <p>{{ trend_analysis }}</p>
    </div>

    <div class="section">
        <h2>关键技术指标</h2>
        {% for indicator in key_indicators %}
        <div class="indicator {{ indicator.signal.lower() }}">
            <strong>{{ indicator.name }}:</strong> {{ indicator.value }}
            <br><small>信号: {{ indicator.signal }} (置信度: {{ indicator.confidence | format_percentage }})</small>
        </div>
        {% endfor %}
    </div>

    <div class="section">
        <h2>支撑阻力位</h2>
        <p><strong>支撑位:</strong> {{ support_resistance.support | join(', ') }}</p>
        <p><strong>阻力位:</strong> {{ support_resistance.resistance | join(', ') }}</p>
    </div>

    <div class="section">
        <h2>动量分析</h2>
        <p>{{ momentum_analysis }}</p>
    </div>

    <div class="section">
        <h2>成交量分析</h2>
        <p>{{ volume_analysis }}</p>
    </div>

    <div class="section">
        <h2>形态识别</h2>
        <p>{{ pattern_recognition }}</p>
    </div>
</body>
</html>
        """.strip()

    def _get_comprehensive_template_content(self) -> str:
        """Get comprehensive template content"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>综合分析报告 - {{ symbol }}</title>
    <style>
        body { font-family: 'Arial', sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .subsection { margin: 15px 0; padding: 10px; background-color: #f9f9f9; border-radius: 3px; }
        .metric { display: inline-block; margin: 5px; padding: 5px; background-color: #fff; border: 1px solid #ddd; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>综合分析报告 - {{ symbol }}</h1>
        <p>生成时间: {{ generated_time | format_datetime }}</p>
        <p>分析模型版本: {{ model_version }}</p>
    </div>

    <!-- 各个分析部分 -->
    {% if technical_analysis %}
    <div class="section">
        <h2>技术面分析</h2>
        {{ technical_analysis | safe }}
    </div>
    {% endif %}

    {% if fundamental_analysis %}
    <div class="section">
        <h2>基本面分析</h2>
        {{ fundamental_analysis | safe }}
    </div>
    {% endif %}

    {% if sentiment_analysis %}
    <div class="section">
        <h2>情绪面分析</h2>
        {{ sentiment_analysis | safe }}
    </div>
    {% endif %}

    {% if market_conditions %}
    <div class="section">
        <h2>市场条件</h2>
        {{ market_conditions | safe }}
    </div>
    {% endif %}

    {% if risk_assessment %}
    <div class="section">
        <h2>风险评估</h2>
        {{ risk_assessment | safe }}
    </div>
    {% endif %}

    {% if strategy_recommendation %}
    <div class="section">
        <h2>策略建议</h2>
        {{ strategy_recommendation | safe }}
    </div>
    {% endif %}

    {% if historical_performance %}
    <div class="section">
        <h2>历史表现</h2>
        {{ historical_performance | safe }}
    </div>
    {% endif %}

    {% if future_projections %}
    <div class="section">
        <h2>未来预测</h2>
        {{ future_projections | safe }}
    </div>
    {% endif %}

    <div class="section">
        <h2>免责声明</h2>
        <p>本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
    </div>
</body>
</html>
        """.strip()

    def _get_generic_template_content(self) -> str:
        """Get generic template content"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>分析报告 - {{ symbol }}</title>
</head>
<body>
    <h1>分析报告 - {{ symbol }}</h1>
    <p>生成时间: {{ generated_time | format_datetime }}</p>

    <div>
        <h2>分析数据</h2>
        <pre>{{ data | tojson(indent=2) }}</pre>
    </div>
</body>
</html>
        """.strip()

    def get_template_config(self, template_name: str) -> TemplateConfig:
        """
        Get template configuration

        Args:
            template_name: Name of the template

        Returns:
            Template configuration
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")

        return self.templates[template_name]

    def update_template(self, template_name: str, new_content: str) -> None:
        """
        Update template content

        Args:
            template_name: Name of the template
            new_content: New template content
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")

        template_config = self.templates[template_name]
        template_path = self.template_dir / template_config.template_path

        # Write new content to file
        template_path.parent.mkdir(parents=True, exist_ok=True)
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

    def list_templates(self) -> List[str]:
        """
        List available templates

        Returns:
            List of template names
        """
        return list(self.templates.keys())

    def add_template(self, name: str, config: TemplateConfig, content: str) -> None:
        """
        Add a new template

        Args:
            name: Template name
            config: Template configuration
            content: Template content
        """
        self.templates[name] = config

        # Save template content
        template_path = self.template_dir / config.template_path
        template_path.parent.mkdir(parents=True, exist_ok=True)
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Update templates configuration file
        self._save_templates_config()

    def _save_templates_config(self) -> None:
        """Save templates configuration to file"""
        config_file = self.template_dir / "templates.yaml"
        configs = {}

        for name, config in self.templates.items():
            if name not in ["standard", "quick_decision", "technical", "comprehensive"]:
                configs[name] = {
                    "name": config.name,
                    "description": config.description,
                    "template_path": config.template_path,
                    "variables": config.variables,
                    "output_formats": [fmt.value for fmt in config.output_formats],
                    "version": config.version
                }

        if configs:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(configs, f, default_flow_style=False, allow_unicode=True)

    def _format_currency(self, value: float) -> str:
        """Format currency value"""
        return f"{value:,.2f}"

    def _format_percentage(self, value: float) -> str:
        """Format percentage value"""
        return f"{value:.2%}"

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime value"""
        return dt.strftime("%Y-%m-%d %H:%M:%S")