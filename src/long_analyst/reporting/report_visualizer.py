"""
Report visualizer for generating charts and visualizations
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
import base64
import io
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from .models import (
    TechnicalAnalysis,
    FundamentalAnalysis,
    SentimentAnalysis,
    MarketDataPoint
)


class ReportVisualizer:
    """Report visualizer for generating charts and visualizations"""

    def __init__(self):
        """Initialize report visualizer"""
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

        # Chart configuration
        self.chart_config = {
            'width': 800,
            'height': 600,
            'dpi': 100,
            'fontsize': 12,
            'color_scheme': {
                'primary': '#1f77b4',
                'secondary': '#ff7f0e',
                'success': '#2ca02c',
                'danger': '#d62728',
                'warning': '#ff9500',
                'info': '#17a2b8'
            }
        }

    async def generate_technical_chart(self, technical_analysis: TechnicalAnalysis) -> str:
        """
        Generate technical analysis chart

        Args:
            technical_analysis: Technical analysis data

        Returns:
            Base64 encoded chart image
        """
        fig = Figure(figsize=(self.chart_config['width']/self.chart_config['dpi'],
                               self.chart_config['height']/self.chart_config['dpi']),
                     dpi=self.chart_config['dpi'])

        # Create subplots
        gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1], width_ratios=[2, 1])
        ax_main = fig.add_subplot(gs[:, 0])
        ax_indicators = fig.add_subplot(gs[0, 1])
        ax_levels = fig.add_subplot(gs[1, 1])
        ax_momentum = fig.add_subplot(gs[2, 1])

        # Main technical analysis chart
        self._plot_technical_overview(ax_main, technical_analysis)

        # Indicators chart
        self._plot_indicators(ax_indicators, technical_analysis)

        # Support/Resistance levels
        self._plot_support_resistance(ax_levels, technical_analysis)

        # Momentum chart
        self._plot_momentum(ax_momentum, technical_analysis)

        fig.tight_layout()
        return self._figure_to_base64(fig)

    async def generate_market_data_chart(self, market_data: List[MarketDataPoint]) -> str:
        """
        Generate market data chart

        Args:
            market_data: Market data points

        Returns:
            Base64 encoded chart image
        """
        if not market_data:
            return ""

        fig = Figure(figsize=(self.chart_config['width']/self.chart_config['dpi'],
                               self.chart_config['height']/self.chart_config['dpi']),
                     dpi=self.chart_config['dpi'])

        # Create subplots
        gs = fig.add_gridspec(2, 1, height_ratios=[3, 1])
        ax_price = fig.add_subplot(gs[0])
        ax_volume = fig.add_subplot(gs[1])

        # Plot price data
        self._plot_price_chart(ax_price, market_data)

        # Plot volume data
        self._plot_volume_chart(ax_volume, market_data)

        fig.tight_layout()
        return self._figure_to_base64(fig)

    async def generate_sentiment_chart(self, sentiment_analysis: SentimentAnalysis) -> str:
        """
        Generate sentiment analysis chart

        Args:
            sentiment_analysis: Sentiment analysis data

        Returns:
            Base64 encoded chart image
        """
        fig = Figure(figsize=(self.chart_config['width']/self.chart_config['dpi'],
                               self.chart_config['height']/self.chart_config['dpi']),
                     dpi=self.chart_config['dpi'])

        # Create subplots
        gs = fig.add_gridspec(2, 2)
        ax_overall = fig.add_subplot(gs[0, :])
        ax_comparison = fig.add_subplot(gs[1, 0])
        ax_confidence = fig.add_subplot(gs[1, 1])

        # Overall sentiment
        self._plot_overall_sentiment(ax_overall, sentiment_analysis)

        # Sentiment comparison
        self._plot_sentiment_comparison(ax_comparison, sentiment_analysis)

        # Confidence chart
        self._plot_sentiment_confidence(ax_confidence, sentiment_analysis)

        fig.tight_layout()
        return self._figure_to_base64(fig)

    async def generate_risk_reward_chart(self, entry_price: float, stop_loss: float, take_profit: float) -> str:
        """
        Generate risk-reward chart

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price

        Returns:
            Base64 encoded chart image
        """
        fig = Figure(figsize=(self.chart_config['width']/self.chart_config['dpi'],
                               self.chart_config['height']/self.chart_config['dpi']),
                     dpi=self.chart_config['dpi'])

        ax = fig.add_subplot(111)

        # Calculate risk and reward
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
        risk_reward_ratio = reward / risk if risk > 0 else 0

        # Create data for visualization
        prices = [stop_loss, entry_price, take_profit]
        labels = ['Stop Loss', 'Entry', 'Take Profit']
        colors = [self.chart_config['color_scheme']['danger'],
                 self.chart_config['color_scheme']['primary'],
                 self.chart_config['color_scheme']['success']]

        # Plot price levels
        bars = ax.bar(labels, prices, color=colors, alpha=0.7)

        # Add value labels on bars
        for bar, price in zip(bars, prices):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'${price:,.0f}',
                   ha='center', va='bottom', fontweight='bold')

        # Add risk-reward information
        ax.text(0.02, 0.98, f'Risk: ${risk:,.0f}', transform=ax.transAxes,
                fontsize=self.chart_config['fontsize'], va='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        ax.text(0.02, 0.90, f'Reward: ${reward:,.0f}', transform=ax.transAxes,
                fontsize=self.chart_config['fontsize'], va='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        ax.text(0.02, 0.82, f'R/R Ratio: {risk_reward_ratio:.2f}', transform=ax.transAxes,
                fontsize=self.chart_config['fontsize'], va='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        ax.set_ylabel('Price ($)')
        ax.set_title('Risk-Reward Analysis', fontsize=self.chart_config['fontsize']+2, fontweight='bold')
        ax.grid(True, alpha=0.3)

        return self._figure_to_base64(fig)

    async def generate_interactive_dashboard(self, technical_analysis: TechnicalAnalysis,
                                          sentiment_analysis: SentimentAnalysis,
                                          market_data: List[MarketDataPoint]) -> str:
        """
        Generate interactive dashboard using Plotly

        Args:
            technical_analysis: Technical analysis data
            sentiment_analysis: Sentiment analysis data
            market_data: Market data points

        Returns:
            HTML string with interactive dashboard
        """
        # Create subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=('Price Chart', 'Sentiment Overview',
                           'Technical Indicators', 'Risk Metrics',
                           'Volume Analysis', 'Market Conditions'),
            specs=[[{"secondary_y": True}, {"type": "pie"}],
                   [{"type": "bar"}, {"type": "indicator"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )

        # Price chart
        if market_data:
            dates = [md.timestamp for md in market_data]
            prices = [md.close for md in market_data]
            volumes = [md.volume for md in market_data]

            fig.add_trace(
                go.Scatter(x=dates, y=prices, name='Price',
                          line=dict(color=self.chart_config['color_scheme']['primary'])),
                row=1, col=1
            )

        # Sentiment pie chart
        if sentiment_analysis:
            sentiment_labels = ['News', 'Social', 'Market']
            sentiment_values = [
                sentiment_analysis.news_sentiment,
                sentiment_analysis.social_sentiment,
                sentiment_analysis.market_sentiment
            ]

            fig.add_trace(
                go.Pie(labels=sentiment_labels, values=sentiment_values,
                       name="Sentiment"),
                row=1, col=2
            )

        # Technical indicators bar chart
        if technical_analysis and technical_analysis.key_indicators:
            indicators = technical_analysis.key_indicators[:5]  # Top 5 indicators
            indicator_names = [ind.name for ind in indicators]
            indicator_values = [ind.value for ind in indicators]

            fig.add_trace(
                go.Bar(x=indicator_names, y=indicator_values,
                       name='Indicators'),
                row=2, col=1
            )

        # Risk metrics gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=75,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Risk Score"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': self.chart_config['color_scheme']['danger']},
                       'steps': [
                           {'range': [0, 50], 'color': self.chart_config['color_scheme']['success']},
                           {'range': [50, 80], 'color': self.chart_config['color_scheme']['warning']},
                           {'range': [80, 100], 'color': self.chart_config['color_scheme']['danger']}
                       ],
                       'threshold': {'line': {'color': "red", 'width': 4},
                                   'thickness': 0.75, 'value': 90}}
            ),
            row=2, col=2
        )

        # Volume analysis
        if market_data:
            fig.add_trace(
                go.Bar(x=dates, y=volumes, name='Volume',
                       marker_color=self.chart_config['color_scheme']['secondary']),
                row=3, col=1
            )

        # Market conditions scatter
        if technical_analysis:
            fig.add_trace(
                go.Scatter(x=['Volatility', 'Momentum', 'Trend'],
                          y=[technical_analysis.volatility * 100,
                             len([i for i in technical_analysis.key_indicators if i.signal == 'BUY']) / len(technical_analysis.key_indicators) * 100,
                             1 if 'UPTREND' in technical_analysis.trend else 0],
                          name='Market Conditions',
                          mode='markers+lines',
                          marker_size=10),
                row=3, col=2
            )

        # Update layout
        fig.update_layout(
            height=1200,
            showlegend=True,
            title_text="Trading Analysis Dashboard",
            title_x=0.5
        )

        return fig.to_html(include_plotlyjs='cdn', div_id="dashboard")

    def _plot_technical_overview(self, ax, technical_analysis: TechnicalAnalysis):
        """Plot technical analysis overview"""
        # Create a simple technical overview visualization
        categories = ['Trend Strength', 'Momentum', 'Volatility']
        values = [
            1.0 if 'STRONG' in technical_analysis.trend else 0.5,
            0.8 if 'BULLISH' in technical_analysis.momentum else 0.2,
            technical_analysis.volatility
        ]

        colors = [self.chart_config['color_scheme']['success'] if val > 0.6 else
                 self.chart_config['color_scheme']['warning'] if val > 0.3 else
                 self.chart_config['color_scheme']['danger'] for val in values]

        bars = ax.bar(categories, values, color=colors, alpha=0.7)

        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.2f}',
                   ha='center', va='bottom', fontweight='bold')

        ax.set_title('Technical Overview', fontsize=self.chart_config['fontsize']+1, fontweight='bold')
        ax.set_ylabel('Score')
        ax.set_ylim(0, 1.2)
        ax.grid(True, alpha=0.3)

    def _plot_indicators(self, ax, technical_analysis: TechnicalAnalysis):
        """Plot technical indicators"""
        if not technical_analysis.key_indicators:
            ax.text(0.5, 0.5, 'No indicators available', ha='center', va='center',
                   transform=ax.transAxes, fontsize=self.chart_config['fontsize'])
            return

        # Take first 5 indicators for visualization
        indicators = technical_analysis.key_indicators[:5]
        names = [ind.name for ind in indicators]
        values = [ind.confidence for ind in indicators]

        colors = [self.chart_config['color_scheme']['success'] if ind.signal == 'BUY' else
                 self.chart_config['color_scheme']['danger'] if ind.signal == 'SELL' else
                 self.chart_config['color_scheme']['warning'] for ind in indicators]

        bars = ax.barh(names, values, color=colors, alpha=0.7)

        # Add value labels
        for bar, value in zip(bars, values):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'{value:.2f}',
                   ha='left', va='center', fontweight='bold')

        ax.set_title('Key Indicators', fontsize=self.chart_config['fontsize']+1, fontweight='bold')
        ax.set_xlabel('Confidence')
        ax.set_xlim(0, 1.1)

    def _plot_support_resistance(self, ax, technical_analysis: TechnicalAnalysis):
        """Plot support and resistance levels"""
        if not technical_analysis.support_levels and not technical_analysis.resistance_levels:
            ax.text(0.5, 0.5, 'No S/R levels available', ha='center', va='center',
                   transform=ax.transAxes, fontsize=self.chart_config['fontsize'])
            return

        levels = []
        labels = []
        colors = []

        for level in technical_analysis.support_levels:
            levels.append(level)
            labels.append(f'S{len(labels)+1}')
            colors.append(self.chart_config['color_scheme']['success'])

        for level in technical_analysis.resistance_levels:
            levels.append(level)
            labels.append(f'R{len(labels)-len(technical_analysis.support_levels)+1}')
            colors.append(self.chart_config['color_scheme']['danger'])

        if levels:
            bars = ax.bar(labels, levels, color=colors, alpha=0.7)

            # Add value labels
            for bar, level in zip(bars, levels):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'${level:,.0f}',
                       ha='center', va='bottom', fontweight='bold')

        ax.set_title('S/R Levels', fontsize=self.chart_config['fontsize']+1, fontweight='bold')
        ax.set_ylabel('Price ($)')
        ax.tick_params(axis='x', rotation=45)

    def _plot_momentum(self, ax, technical_analysis: TechnicalAnalysis):
        """Plot momentum indicator"""
        momentum_score = 0
        if technical_analysis.momentum == 'STRONG_BULLISH':
            momentum_score = 1.0
        elif technical_analysis.momentum == 'BULLISH':
            momentum_score = 0.7
        elif technical_analysis.momentum == 'BEARISH':
            momentum_score = 0.3
        elif technical_analysis.momentum == 'STRONG_BEARISH':
            momentum_score = 0.0
        else:
            momentum_score = 0.5

        # Create gauge-like visualization
        theta = np.linspace(0, np.pi, 100)
        r = np.ones_like(theta)

        # Background arc
        ax.plot(theta, r, color='lightgray', linewidth=10)

        # Momentum arc
        momentum_theta = np.linspace(0, momentum_score * np.pi, 50)
        momentum_r = np.ones_like(momentum_theta)
        color = self.chart_config['color_scheme']['success'] if momentum_score > 0.6 else \
                self.chart_config['color_scheme']['warning'] if momentum_score > 0.4 else \
                self.chart_config['color_scheme']['danger']

        ax.plot(momentum_theta, momentum_r, color=color, linewidth=10)

        # Add momentum text
        ax.text(0.5, 0.7, f'{momentum_score:.1%}', ha='center', va='center',
                transform=ax.transAxes, fontsize=self.chart_config['fontsize']+4,
                fontweight='bold')

        ax.text(0.5, 0.5, 'Momentum', ha='center', va='center',
                transform=ax.transAxes, fontsize=self.chart_config['fontsize'])

        ax.set_xlim(0, np.pi)
        ax.set_ylim(0, 1.5)
        ax.set_title('Momentum', fontsize=self.chart_config['fontsize']+1, fontweight='bold')
        ax.set_xticks([])
        ax.set_yticks([])

    def _plot_price_chart(self, ax, market_data: List[MarketDataPoint]):
        """Plot price chart"""
        dates = [md.timestamp for md in market_data]
        closes = [md.close for md in market_data]
        highs = [md.high for md in market_data]
        lows = [md.low for md in market_data]

        # Plot candlestick-like chart
        for i, (date, close, high, low) in enumerate(zip(dates, closes, highs, lows)):
            color = self.chart_config['color_scheme']['success'] if closes[i] >= closes[i-1] if i > 0 else self.chart_config['color_scheme']['danger']

            # High-Low line
            ax.plot([date, date], [low, high], color=color, linewidth=1)

            # Open-Close bar
            if i > 0:
                open_price = closes[i-1]
                ax.bar(date, abs(close - open_price), bottom=min(open_price, close),
                      color=color, width=0.8, alpha=0.7)

        ax.set_title('Price Chart', fontsize=self.chart_config['fontsize']+1, fontweight='bold')
        ax.set_ylabel('Price ($)')
        ax.grid(True, alpha=0.3)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    def _plot_volume_chart(self, ax, market_data: List[MarketDataPoint]):
        """Plot volume chart"""
        dates = [md.timestamp for md in market_data]
        volumes = [md.volume for md in market_data]

        # Color bars based on price change
        colors = []
        for i in range(1, len(market_data)):
            if market_data[i].close >= market_data[i-1].close:
                colors.append(self.chart_config['color_scheme']['success'])
            else:
                colors.append(self.chart_config['color_scheme']['danger'])

        if colors:
            ax.bar(dates[1:], volumes[1:], color=colors, alpha=0.7)

        ax.set_title('Volume', fontsize=self.chart_config['fontsize']+1, fontweight='bold')
        ax.set_ylabel('Volume')
        ax.grid(True, alpha=0.3)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    def _plot_overall_sentiment(self, ax, sentiment_analysis: SentimentAnalysis):
        """Plot overall sentiment"""
        sentiment_map = {
            'VERY_BULLISH': 1.0,
            'BULLISH': 0.7,
            'NEUTRAL': 0.5,
            'BEARISH': 0.3,
            'VERY_BEARISH': 0.0
        }

        sentiment_score = sentiment_map.get(sentiment_analysis.overall_sentiment, 0.5)
        confidence = sentiment_analysis.confidence

        # Create sentiment visualization
        categories = ['Bearish', 'Neutral', 'Bullish']
        values = [0.3, 0.5, 0.7]
        current_value = sentiment_score

        # Plot sentiment scale
        ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)
        ax.scatter(['Current'], [current_value], s=200, c=self.chart_config['color_scheme']['primary'],
                  alpha=confidence, zorder=5)

        ax.set_xlim(-0.5, 0.5)
        ax.set_ylim(0, 1)
        ax.set_title('Overall Sentiment', fontsize=self.chart_config['fontsize']+1, fontweight='bold')
        ax.set_ylabel('Sentiment Score')
        ax.grid(True, alpha=0.3)

    def _plot_sentiment_comparison(self, ax, sentiment_analysis: SentimentAnalysis):
        """Plot sentiment comparison"""
        categories = ['News', 'Social', 'Market']
        values = [
            sentiment_analysis.news_sentiment,
            sentiment_analysis.social_sentiment,
            sentiment_analysis.market_sentiment
        ]

        colors = [self.chart_config['color_scheme']['success'] if v > 0 else
                 self.chart_config['color_scheme']['danger'] for v in values]

        bars = ax.bar(categories, values, color=colors, alpha=0.7)

        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.2f}',
                   ha='center', va='bottom' if height > 0 else 'top',
                   fontweight='bold')

        ax.set_title('Sentiment Sources', fontsize=self.chart_config['fontsize']+1, fontweight='bold')
        ax.set_ylabel('Score')
        ax.set_ylim(-1, 1)
        ax.grid(True, alpha=0.3)

    def _plot_sentiment_confidence(self, ax, sentiment_analysis: SentimentAnalysis):
        """Plot sentiment confidence"""
        confidence = sentiment_analysis.confidence

        # Create confidence gauge
        theta = np.linspace(0, 2 * np.pi, 100)
        r = np.ones_like(theta)

        # Background circle
        ax.plot(theta, r, color='lightgray', linewidth=10)

        # Confidence arc
        confidence_theta = np.linspace(0, confidence * 2 * np.pi, 50)
        confidence_r = np.ones_like(confidence_theta)
        color = self.chart_config['color_scheme']['success'] if confidence > 0.7 else \
                self.chart_config['color_scheme']['warning'] if confidence > 0.4 else \
                self.chart_config['color_scheme']['danger']

        ax.plot(confidence_theta, confidence_r, color=color, linewidth=10)

        # Add confidence text
        ax.text(0, 0, f'{confidence:.1%}', ha='center', va='center',
                fontsize=self.chart_config['fontsize']+4, fontweight='bold')

        ax.set_title('Confidence', fontsize=self.chart_config['fontsize']+1, fontweight='bold')
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])

    def _figure_to_base64(self, fig: Figure) -> str:
        """Convert matplotlib figure to base64 string"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=self.chart_config['dpi'], bbox_inches='tight')
        buffer.seek(0)

        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()

        plt.close(fig)

        return f"data:image/png;base64,{image_base64}"