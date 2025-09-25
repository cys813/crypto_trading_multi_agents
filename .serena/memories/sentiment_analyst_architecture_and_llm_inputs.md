# Sentiment Analyst: Architecture and LLM Inputs

## 1. Overall Architecture: Hybrid Analysis Model

The `SentimentAnalyst` employs a sophisticated **"Traditional Rules + AI Enhanced"** hybrid model. This architecture combines the stability and interpretability of rule-based systems with the deep contextual understanding of Large Language Models (LLMs).

- **`SentimentAnalyst` Class (`src/crypto_trading_agents/agents/analysts/sentiment_analyst.py`)**:
  - Contains the core business logic specific to sentiment analysis.
  - Manages data collection from various sources (Twitter, Reddit, news, etc.).
  - Implements the traditional, rule-based analysis algorithms.

- **`StandardAIAnalysisMixin` Class (`src/crypto_trading_agents/services/ai_analysis_mixin.py`)**:
  - A reusable component that provides standardized AI analysis capabilities to any agent.
  - `SentimentAnalyst` inherits from this mixin to gain access to the AI-enhancement workflow.
  - This design decouples general AI functionality from specific analyst logic, promoting code reuse and modularity.

## 2. End-to-End Analysis Workflow

The process flows through several distinct stages:

1.  **Data Collection (`collect_data`)**: Gathers raw data from multiple sources. *Note: Currently uses simulated data.*
2.  **Analysis Entry (`analyze`)**: The main entry point that orchestrates the entire hybrid analysis by calling `analyze_with_ai_enhancement`.
3.  **Traditional Analysis (`_traditional_analyze`)**:
    - Performs a rule-based analysis on the raw data.
    - Calculates quantitative scores, identifies trends, assesses risk, and generates a preliminary confidence score.
4.  **AI-Enhanced Analysis (via Mixin)**:
    - **Prompt Construction (`_build_sentiment_analysis_prompt`)**: This is a critical step. It combines the **raw data summary** and the **traditional analysis results** into a rich, detailed prompt for the LLM. It explicitly asks the AI to evaluate deeper concepts like market psychology, emotional cycles, and anomaly detection.
    - **LLM Call**: The prompt is sent to the configured LLM via the central `LLMService`.
    - **Result Parsing & Fusion (`_parse_ai_response`, `_combine_analyses`)**: The LLM's JSON response is parsed. The AI's insights are then fused with the traditional analysis, and a final, weighted confidence score is calculated. The system includes robust error handling to gracefully degrade to a traditional-only analysis if the AI fails.

## 3. Information Collected for LLM Analysis

The LLM is provided with a comprehensive context package containing two main categories of information:

### A. Raw Data Summary

A condensed version of the data collected directly from sources:
- **Social Media**: Twitter, Reddit, Telegram sentiment metrics.
- **News**: Sentiment from news articles.
- **Market Indicators**: Fear & Greed Index, Social Volume data.
- **Human Factor**: Key Opinion Leader (KOL) statements.

### B. Traditional Analysis Summary

The complete output from the rule-based analysis engine:
- **Per-Source Breakdown**: Analysis for each individual data source.
- **Overall Sentiment**: A single, weighted score and directional bias (Bullish/Bearish/Neutral).
- **Temporal Dynamics**: Analysis of sentiment trends over time.
- **Risk Assessment**: Evaluation of market emotional state (e.g., Extreme Greed).
- **Key Signals**: A list of identified important events or shifts.
- **Metadata**: An assessment of the input data's quality and the confidence level of the traditional analysis itself.

By providing both the "what" (raw data) and the "so what" (traditional analysis), the system enables the LLM to perform a high-level, meta-analysis, leading to deeper and more nuanced insights.
