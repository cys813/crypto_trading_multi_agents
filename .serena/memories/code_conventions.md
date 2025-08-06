# Code Conventions - Crypto Trading Agents

## Python Style Guidelines

### General Principles
- **PEP 8 Compliance**: Follow PEP 8 style guidelines
- **Type Hints**: Use type hints for all function signatures and important variables
- **Docstrings**: Comprehensive docstrings for all public functions and classes
- **English Comments**: All comments and docstrings in English for international collaboration
- **Descriptive Names**: Use clear, descriptive variable and function names

### Code Formatting
```python
# Good example
def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI) for a given price series.
    
    Args:
        prices: List of price values
        period: RSI calculation period (default: 14)
    
    Returns:
        RSI value between 0 and 100
    
    Raises:
        ValueError: If prices list is empty or period is invalid
    """
    if not prices or len(prices) < period:
        raise ValueError("Insufficient price data for RSI calculation")
    
    # Implementation here
    pass

# Bad example
def calc_rsi(p, per=14):
    # calculate rsi
    if not p: return 0
    # implementation
    pass
```

### Import Organization
```python
# Standard library imports
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Third-party imports
import pandas as pd
import numpy as np
import streamlit as st
from dotenv import load_dotenv

# Local imports
from crypto_trading_agents.config import get_config
from crypto_trading_agents.agents.base import BaseAgent
from crypto_trading_agents.utils.logger import get_logger
```

## Naming Conventions

### Variables and Functions
- **snake_case**: For all variables and functions
- **descriptive_names**: Use clear, meaningful names
- **constants**: UPPER_CASE for constants

```python
# Good
max_position_size = 0.1
stop_loss_percentage = 0.05
def calculate_technical_indicators(price_data: pd.DataFrame) -> Dict[str, float]:

# Bad
maxPos = 0.1
sl_perc = 0.05
def calc_tech_ind(df) -> dict:
```

### Classes
- **PascalCase**: For class names
- **descriptive_names**: Clear, meaningful class names

```python
# Good
class TechnicalAnalyst(BaseAgent):
class MarketDataManager:
class RiskAssessmentCalculator:

# Bad
class techanalyst:
class MgrData:
class riskCalc:
```

### Files and Directories
- **snake_case**: For file and directory names
- **descriptive_names**: Clear, meaningful names

```python
# Good
technical_analyst.py
market_data_manager.py
risk_management_utils.py

# Bad
tech_analyst.py
mgr_data.py
risk_utils.py
```

## Type Hints

### Function Signatures
```python
from typing import Dict, List, Optional, Union, Any, Callable
from datetime import datetime
import pandas as pd

# Complete type hints
def analyze_market_data(
    symbol: str,
    timeframe: str,
    indicators: List[str],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    pass

# Return type hints for complex structures
def get_trading_signals(analysis_result: Dict[str, Any]) -> List[Dict[str, Union[str, float, bool]]]:
    pass
```

### Custom Type Definitions
```python
from typing import TypedDict, Protocol

class AnalysisResult(TypedDict):
    analysis_id: str
    timestamp: str
    symbol: str
    results: Dict[str, Any]
    confidence_score: float
    trading_signals: List[Dict[str, Any]]

class DataSourceProtocol(Protocol):
    async def fetch_data(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        ...
    
    def get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        ...
```

## Error Handling

### Exception Handling Patterns
```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def fetch_api_data(url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Fetch data from API with proper error handling.
    
    Args:
        url: API endpoint URL
        params: Request parameters
    
    Returns:
        API response data or None if failed
    """
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for {url}: {e}")
        return None
    
    except ValueError as e:
        logger.error(f"Failed to parse API response from {url}: {e}")
        return None
    
    except Exception as e:
        logger.error(f"Unexpected error fetching data from {url}: {e}")
        return None
```

### Custom Exceptions
```python
class CryptoTradingError(Exception):
    """Base exception for crypto trading operations"""
    pass

class DataFetchError(CryptoTradingError):
    """Exception raised when data fetching fails"""
    pass

class AnalysisError(CryptoTradingError):
    """Exception raised when analysis fails"""
    pass

class ConfigurationError(CryptoTradingError):
    """Exception raised when configuration is invalid"""
    pass
```

## Logging Standards

### Logger Setup
```python
import logging
from typing import Optional

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    if level:
        logger.setLevel(getattr(logging, level.upper()))
    
    return logger
```

### Logging Usage
```python
logger = get_logger(__name__)

def process_data(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    logger.info(f"Processing data for symbol: {data.get('symbol', 'unknown')}")
    
    try:
        # Processing logic
        result = analyze_data(data)
        logger.debug(f"Analysis completed successfully: {result}")
        return result
    
    except Exception as e:
        logger.error(f"Data processing failed: {e}")
        return None
```

## Configuration Management

### Configuration Patterns
```python
from typing import Dict, Any, Optional
import os
from dataclasses import dataclass

@dataclass
class TradingConfig:
    max_position_size: float = 0.1
    stop_loss_percentage: float = 0.05
    take_profit_percentage: float = 0.15
    max_leverage: int = 3
    
    @classmethod
    def from_env(cls) -> 'TradingConfig':
        return cls(
            max_position_size=float(os.getenv('MAX_POSITION_SIZE', '0.1')),
            stop_loss_percentage=float(os.getenv('STOP_LOSS_PERCENTAGE', '0.05')),
            take_profit_percentage=float(os.getenv('TAKE_PROFIT_PERCENTAGE', '0.15')),
            max_leverage=int(os.getenv('MAX_LEVERAGE', '3'))
        )
    
    def validate(self) -> bool:
        return (
            0 < self.max_position_size <= 1.0 and
            0 < self.stop_loss_percentage <= 1.0 and
            0 < self.take_profit_percentage <= 1.0 and
            self.max_leverage > 0
        )
```

## Async/Await Patterns

### Async Function Design
```python
import asyncio
from typing import List, Dict, Any
import aiohttp

class DataSourceManager:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_multiple_sources(self, symbols: List[str]) -> Dict[str, Any]:
        """Fetch data from multiple sources concurrently"""
        tasks = [self.fetch_single_source(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            symbol: result for symbol, result in zip(symbols, results)
            if not isinstance(result, Exception)
        }
    
    async def fetch_single_source(self, symbol: str) -> Dict[str, Any]:
        """Fetch data from a single source"""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        try:
            async with self.session.get(f"https://api.example.com/{symbol}") as response:
                response.raise_for_status()
                return await response.json()
        
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            raise
```

## Testing Standards

### Test Structure
```python
import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

class TestTechnicalAnalyst:
    """Test suite for TechnicalAnalyst class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.analyst = TechnicalAnalyst()
        self.test_data = {
            'prices': [100, 102, 101, 103, 105],
            'volume': [1000, 1200, 1100, 1300, 1400]
        }
    
    def test_calculate_rsi_valid_data(self):
        """Test RSI calculation with valid data"""
        result = self.analyst.calculate_rsi(self.test_data['prices'])
        
        assert isinstance(result, float)
        assert 0 <= result <= 100
    
    def test_calculate_rsi_invalid_data(self):
        """Test RSI calculation with invalid data"""
        with pytest.raises(ValueError):
            self.analyst.calculate_rsi([])
    
    @patch('requests.get')
    def test_fetch_market_data(self, mock_get):
        """Test market data fetching"""
        mock_response = Mock()
        mock_response.json.return_value = {'price': 50000, 'volume': 1000000}
        mock_get.return_value = mock_response
        
        result = self.analyst.fetch_market_data('BTC/USDT')
        
        assert result['price'] == 50000
        mock_get.assert_called_once()
```

### Async Testing
```python
import pytest
import asyncio
from unittest.mock import AsyncMock

class TestAsyncDataSource:
    """Test suite for async data sources"""
    
    @pytest.mark.asyncio
    async def test_fetch_data_success(self):
        """Test successful data fetching"""
        data_source = AsyncDataSource()
        data_source.session = AsyncMock()
        
        mock_response = AsyncMock()
        mock_response.json.return_value = {'symbol': 'BTC/USDT', 'price': 50000}
        mock_response.raise_for_status = Mock()
        
        data_source.session.get.return_value.__aenter__.return_value = mock_response
        
        result = await data_source.fetch_data('BTC/USDT')
        
        assert result['symbol'] == 'BTC/USDT'
        assert result['price'] == 50000
```

## Documentation Standards

### Docstring Format (Google Style)
```python
def analyze_trading_signal(
    signal_data: Dict[str, Any],
    market_context: Dict[str, Any],
    risk_params: Dict[str, float]
) -> Dict[str, Any]:
    """
    Analyze trading signal with market context and risk parameters.
    
    This function evaluates trading signals by combining technical analysis
    with market sentiment and risk management principles.
    
    Args:
        signal_data: Dictionary containing signal information including:
            - signal_type: Type of signal (buy/sell/hold)
            - strength: Signal strength (0-1)
            - timestamp: Signal generation time
        market_context: Dictionary containing market context data including:
            - volatility: Current market volatility
            - trend: Market trend direction
            - volume: Trading volume
        risk_params: Dictionary containing risk parameters including:
            - max_position_size: Maximum position size as percentage
            - stop_loss: Stop loss percentage
            - take_profit: Take profit percentage
    
    Returns:
        Dictionary containing analysis results:
            - recommendation: Final trading recommendation
            - confidence: Confidence level (0-1)
            - position_size: Recommended position size
            - entry_price: Recommended entry price
            - stop_loss: Recommended stop loss price
            - take_profit: Recommended take profit price
    
    Raises:
        ValueError: If input data is invalid or missing required fields
        AnalysisError: If analysis fails due to computational errors
    
    Example:
        >>> signal = {'signal_type': 'buy', 'strength': 0.8, 'timestamp': '2024-01-01'}
        >>> context = {'volatility': 0.2, 'trend': 'bullish', 'volume': 1000000}
        >>> risk = {'max_position_size': 0.1, 'stop_loss': 0.05, 'take_profit': 0.15}
        >>> result = analyze_trading_signal(signal, context, risk)
        >>> print(result['recommendation'])
        'buy'
    """
    # Implementation here
    pass
```

## Security Best Practices

### API Key Management
```python
import os
from typing import Optional
from cryptography.fernet import Fernet

class ApiKeyManager:
    """Secure API key management"""
    
    def __init__(self):
        self.key_file = os.path.expanduser("~/.crypto_trading_agents/encryption_key.key")
        self.encrypted_keys_file = os.path.expanduser("~/.crypto_trading_agents/encrypted_keys.json")
        self._encryption_key = self._load_or_create_key()
    
    def _load_or_create_key(self) -> bytes:
        """Load existing encryption key or create new one"""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key
    
    def store_api_key(self, service: str, api_key: str) -> None:
        """Securely store API key"""
        fernet = Fernet(self._encryption_key)
        encrypted_key = fernet.encrypt(api_key.encode())
        
        # Load existing keys
        keys = {}
        if os.path.exists(self.encrypted_keys_file):
            with open(self.encrypted_keys_file, 'r') as f:
                import json
                keys = json.load(f)
        
        # Add new key
        keys[service] = encrypted_key.decode()
        
        # Save keys
        os.makedirs(os.path.dirname(self.encrypted_keys_file), exist_ok=True)
        with open(self.encrypted_keys_file, 'w') as f:
            import json
            json.dump(keys, f, indent=2)
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Retrieve API key securely"""
        if not os.path.exists(self.encrypted_keys_file):
            return None
        
        with open(self.encrypted_keys_file, 'r') as f:
            import json
            keys = json.load(f)
        
        if service not in keys:
            return None
        
        fernet = Fernet(self._encryption_key)
        encrypted_key = keys[service].encode()
        return fernet.decrypt(encrypted_key).decode()
```

## Performance Guidelines

### Memory Management
```python
import gc
from typing import Generator, Any

class DataProcessor:
    """Memory-efficient data processor"""
    
    def process_large_dataset(self, data_file: str) -> Generator[Dict[str, Any], None, None]:
        """
        Process large dataset in chunks to avoid memory issues.
        
        Args:
            data_file: Path to data file
            
        Yields:
            Processed data chunks
        """
        chunk_size = 1000  # Process 1000 records at a time
        
        for chunk in pd.read_csv(data_file, chunksize=chunk_size):
            processed_chunk = self._process_chunk(chunk)
            yield processed_chunk
            
            # Explicit cleanup
            del chunk
            gc.collect()
    
    def _process_chunk(self, chunk: pd.DataFrame) -> Dict[str, Any]:
        """Process a single chunk of data"""
        # Process chunk logic here
        return {
            'count': len(chunk),
            'summary': chunk.describe(),
            'processed_at': datetime.now().isoformat()
        }
```

### Caching Strategy
```python
import time
from functools import wraps
from typing import Any, Dict, Optional
import hashlib
import json

class CacheManager:
    """Intelligent caching system"""
    
    def __init__(self, cache_dir: str = "~/.crypto_trading_agents/cache", ttl: int = 300):
        self.cache_dir = cache_dir
        self.ttl = ttl  # Time to live in seconds
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        key_data = {
            'func': func_name,
            'args': args,
            'kwargs': kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_file(self, cache_key: str) -> str:
        """Get cache file path"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _is_cache_valid(self, cache_file: str) -> bool:
        """Check if cache is still valid"""
        if not os.path.exists(cache_file):
            return False
        
        file_age = time.time() - os.path.getmtime(cache_file)
        return file_age < self.ttl
    
    def cache_result(self, func):
        """Decorator to cache function results"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = self._get_cache_key(func.__name__, *args, **kwargs)
            cache_file = self._get_cache_file(cache_key)
            
            # Try to get from cache
            if self._is_cache_valid(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        return json.load(f)
                except Exception:
                    pass  # Cache corrupted, continue to recompute
            
            # Compute result
            result = func(*args, **kwargs)
            
            # Save to cache
            try:
                with open(cache_file, 'w') as f:
                    json.dump(result, f)
            except Exception:
                pass  # Cache save failed, continue
            
            return result
        
        return wrapper
```

## Web Development Standards

### Streamlit Components
```python
import streamlit as st
from typing import Dict, Any, Optional

class AnalysisForm:
    """Streamlit analysis form component"""
    
    def __init__(self):
        self.form_key = "analysis_form"
    
    def render(self) -> Dict[str, Any]:
        """Render analysis form and return form data"""
        with st.form(key=self.form_key):
            # Symbol input
            symbol = st.text_input(
                "交易对符号",
                value="BTC/USDT",
                help="输入交易对符号，如: BTC/USDT, ETH/USDT"
            )
            
            # Exchange selection
            exchange = st.selectbox(
                "交易所",
                options=["binance", "coinbase", "okx", "huobi"],
                index=0,
                help="选择数据源交易所"
            )
            
            # Analysis level
            analysis_level = st.slider(
                "分析级别",
                min_value=1,
                max_value=5,
                value=3,
                step=1,
                help="1=快速分析, 3=标准分析, 5=深度分析"
            )
            
            # Agent selection
            agents = st.multiselect(
                "分析代理",
                options=["technical", "onchain", "sentiment", "defi", "market_maker"],
                default=["technical", "sentiment"],
                help="选择要启用的分析代理"
            )
            
            # Submit button
            submitted = st.form_submit_button("开始分析")
            
            if submitted:
                if not symbol:
                    st.error("请输入交易对符号")
                    return {'submitted': False}
                
                if not agents:
                    st.error("请至少选择一个分析代理")
                    return {'submitted': False}
                
                return {
                    'submitted': True,
                    'symbol': symbol.upper(),
                    'exchange': exchange,
                    'analysis_level': analysis_level,
                    'agents': agents
                }
        
        return {'submitted': False}
```