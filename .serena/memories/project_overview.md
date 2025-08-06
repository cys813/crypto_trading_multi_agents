# Crypto Trading Agents - Project Overview

## Project Purpose
Crypto Trading Agents is a sophisticated multi-agent cryptocurrency trading analysis system that provides AI-powered market analysis, risk assessment, and trading signals for cryptocurrency markets.

## Core Features
- **Multi-Agent Architecture**: Specialized AI agents for technical analysis, on-chain analysis, sentiment analysis, DeFi analysis, and market maker analysis
- **Modern Web Interface**: Streamlit-based responsive web application with real-time progress tracking
- **Comprehensive Data Integration**: Multiple data sources including CoinGecko, Glassnode, LunarCrush, and major exchanges
- **AI Model Support**: Integration with multiple LLM providers (OpenAI, Anthropic, Google AI, DeepSeek)
- **Risk Management**: Multi-layered risk assessment with debate-style analysis

## Technical Stack
- **Backend**: Python 3.10+ with async/await support
- **Web Framework**: Streamlit for the user interface
- **AI/ML**: OpenAI, Anthropic, LangChain, various ML models
- **Data Processing**: Pandas, NumPy, scikit-learn, statsmodels
- **Cryptocurrency**: CCXT, Web3.py, Solana.py, pycoingecko
- **Database**: MongoDB, Redis, SQLAlchemy support
- **Visualization**: Plotly, Matplotlib, Seaborn
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Code Quality**: black, flake8, mypy, isort

## Project Structure
```
crypto_trading_agents/
├── crypto_trading_agents/          # Main code directory
│   ├── agents/                     # Agent implementations
│   │   ├── analysts/              # Analysis agents (technical, on-chain, sentiment, etc.)
│   │   ├── managers/              # Management agents
│   │   ├── researchers/           # Research agents
│   │   ├── risk_managers/         # Risk management agents (includes debators)
│   │   └── traders/               # Trading agents
│   ├── config/                    # Configuration management
│   ├── data_sources/              # Data source implementations
│   ├── database/                  # Database models and utilities
│   ├── llm/                       # LLM adapters
│   ├── tools/                     # Utility functions
│   ├── web/                       # Web interface components
│   │   ├── components/            # Streamlit components
│   │   └── utils/                 # Web utilities
│   └── utils/                     # General utilities
├── data/                          # Data directory
├── docs/                          # Documentation
├── examples/                      # Example code and usage samples
├── scripts/                       # Utility scripts
├── tests/                         # Test files
└── web/                           # Web interface components
```

## Key Entry Points
- **Web Interface**: `python start_web.py` or `python crypto_trading_agents/web/app.py`
- **Main Config**: `crypto_trading_agents/default_config.py`
- **Requirements**: `requirements.txt`, `requirements_web.txt`

## Supported Cryptocurrencies
- **Major Coins**: BTC, ETH, BNB, SOL, ADA, DOT, MATIC
- **DeFi Blue Chips**: UNI, AAVE, LINK, COMP, CRV
- **Exchanges**: Binance, Coinbase, FTX, OKX, Huobi

## Analysis Capabilities
- **Technical Analysis**: RSI, MACD, Bollinger Bands, Ichimoku, pattern recognition
- **On-Chain Analysis**: Whale activity, address metrics, network health
- **Sentiment Analysis**: Social media, news sentiment, fear/greed index
- **DeFi Analysis**: TVL, liquidity pools, yield farming
- **Market Maker Analysis**: Order book depth, liquidity, spread analysis

## Development Status
- **Version**: 0.1.0 (active development)
- **License**: Apache 2.0
- **Python Requirement**: 3.10+
- **Deployment**: Docker support available
- **Testing**: Comprehensive test suite with pytest

## Risk Disclaimer
This system is for educational and research purposes only. Cryptocurrency trading involves substantial risk, and AI predictions have inherent uncertainties.