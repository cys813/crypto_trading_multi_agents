# Project Architecture - Crypto Trading Agents

## High-Level Architecture

### System Overview
The Crypto Trading Agents system is built on a multi-agent architecture where specialized AI agents collaborate to provide comprehensive cryptocurrency market analysis. The system is designed with clear separation of concerns, scalability, and maintainability in mind.

### Architecture Layers
```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │  Header │ │ Sidebar │ │  Form   │ │ Results │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Application Service Layer                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ Session │ │ Progress │ │ Analysis│ │ Config  │          │
│  │ Manager │ │ Tracker │ │ Runner  │ │ Manager │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Multi-Agent Layer                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ Analysts│ │Researchers│ │Risk Mgmt│ │ Decision │          │
│  │   Team  │ │   Team   │ │   Team   │ │   Team   │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Data Service Layer                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ Market  │ │ Onchain │ │Sentiment│ │  DeFi   │          │
│  │  Data   │ │  Data   │ │  Data   │ │  Data   │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Agent System

#### Agent Hierarchy
```
BaseAgent (Abstract Base Class)
├── AnalysisAgent
│   ├── TechnicalAnalyst
│   ├── OnchainAnalyst
│   ├── SentimentAnalyst
│   ├── DeFiAnalyst
│   └── MarketMakerAnalyst
├── ResearchAgent
│   ├── BullResearcher
│   └── BearResearcher
├── RiskManagerAgent
│   ├── CryptoRiskManager
│   ├── AggressiveDebator
│   ├── ConservativeDebator
│   └── NeutralDebator
└── TradingAgent
    └── CryptoTrader
```

#### Agent Communication
```python
from typing import Dict, Any, List
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.state = {}
    
    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform analysis on provided data"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass
    
    def communicate(self, target_agent: 'BaseAgent', message: Dict[str, Any]) -> Dict[str, Any]:
        """Communicate with another agent"""
        # Agent communication logic
        pass

class AgentOrchestrator:
    """Coordinates agent interactions and workflows"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_queue = []
        self.results_cache = {}
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        self.agents[agent.name] = agent
    
    async def run_analysis(self, request: AnalysisRequest) -> AnalysisResult:
        """Run coordinated analysis with multiple agents"""
        # Step 1: Data collection and preparation
        data = await self._collect_data(request)
        
        # Step 2: Parallel agent analysis
        tasks = []
        for agent_name in request.agents:
            if agent_name in self.agents:
                task = self.agents[agent_name].analyze(data)
                tasks.append(task)
        
        agent_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Step 3: Result synthesis and debate
        final_result = await self._synthesize_results(agent_results, request)
        
        return final_result
```

### 2. Data Layer Architecture

#### Data Source Abstraction
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class BaseDataSource(ABC):
    """Abstract base class for all data sources"""
    
    def __init__(self, api_key: Optional[str] = None, demo_mode: bool = False):
        self.api_key = api_key
        self.demo_mode = demo_mode
        self.cache = {}
        self.rate_limiter = RateLimiter()
    
    @abstractmethod
    async def fetch_data(self, symbol: str, timeframe: str = '1d') -> Dict[str, Any]:
        """Fetch data from the source"""
        pass
    
    @abstractmethod
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported trading symbols"""
        pass
    
    def get_cached_data(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get cached data if available and not expired"""
        cache_key = f"{symbol}_{timeframe}"
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return data
        return None
    
    def cache_data(self, symbol: str, timeframe: str, data: Dict[str, Any]):
        """Cache data with timestamp"""
        cache_key = f"{symbol}_{timeframe}"
        self.cache[cache_key] = (data, time.time())

class DataSourceManager:
    """Manages multiple data sources with failover support"""
    
    def __init__(self):
        self.sources = {
            'market': [
                CoinGeckoDataSource(),
                BinanceDataSource(),
                CoinMarketCapDataSource()
            ],
            'onchain': [
                GlassnodeDataSource(),
                IntoTheBlockDataSource()
            ],
            'sentiment': [
                LunarCrushDataSource(),
                SantimentDataSource()
            ],
            'defi': [
                DeFiLlamaDataSource(),
                UniswapDataSource()
            ]
        }
        self.cache_manager = CacheManager()
    
    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get market data with failover between sources"""
        for source in self.sources['market']:
            try:
                data = await source.fetch_data(symbol)
                if data:
                    return data
            except Exception as e:
                logger.warning(f"Failed to fetch from {source.__class__.__name__}: {e}")
        
        raise DataFetchError(f"All market data sources failed for {symbol}")
```

### 3. Configuration Management

#### Configuration Hierarchy
```python
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import json
import os

@dataclass
class SystemConfig:
    """System-wide configuration"""
    version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    max_workers: int = 4
    timeout: int = 300

@dataclass
class LLMConfig:
    """LLM provider configuration"""
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: str = ""
    base_url: str = ""
    max_tokens: int = 4000
    temperature: float = 0.7

@dataclass
class TradingConfig:
    """Trading configuration"""
    default_symbol: str = "BTC/USDT"
    default_timeframe: str = "1h"
    risk_per_trade: float = 0.02
    max_position_size: float = 0.1
    stop_loss: float = 0.05
    take_profit: float = 0.15
    max_leverage: int = 3

@dataclass
class CryptoConfig:
    """Cryptocurrency-specific configuration"""
    supported_exchanges: List[str] = field(default_factory=lambda: ["binance", "coinbase", "okx"])
    supported_chains: List[str] = field(default_factory=lambda: ["ethereum", "bitcoin", "solana"])
    defi_protocols: List[str] = field(default_factory=lambda: ["uniswap", "aave", "compound"])

@dataclass
class AnalysisConfig:
    """Analysis configuration"""
    technical_indicators: List[str] = field(default_factory=lambda: ["rsi", "macd", "bollinger_bands"])
    onchain_metrics: List[str] = field(default_factory=lambda: ["active_addresses", "transaction_count"])
    sentiment_sources: List[str] = field(default_factory=lambda: ["twitter", "reddit", "news"])
    timeframes: List[str] = field(default_factory=lambda: ["1m", "5m", "15m", "1h", "4h", "1d"])

class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.expanduser("~/.crypto_trading_agents/config.json")
        self.system = SystemConfig()
        self.llm = LLMConfig()
        self.trading = TradingConfig()
        self.crypto = CryptoConfig()
        self.analysis = AnalysisConfig()
    
    def load_config(self) -> bool:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                
                # Update configurations
                if 'system' in config_data:
                    self.system = SystemConfig(**config_data['system'])
                if 'llm' in config_data:
                    self.llm = LLMConfig(**config_data['llm'])
                if 'trading' in config_data:
                    self.trading = TradingConfig(**config_data['trading'])
                if 'crypto' in config_data:
                    self.crypto = CryptoConfig(**config_data['crypto'])
                if 'analysis' in config_data:
                    self.analysis = AnalysisConfig(**config_data['analysis'])
                
                return True
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
        
        return False
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            config_data = {
                'system': self.system.__dict__,
                'llm': self.llm.__dict__,
                'trading': self.trading.__dict__,
                'crypto': self.crypto.__dict__,
                'analysis': self.analysis.__dict__
            }
            
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get_env_config(self) -> Dict[str, Any]:
        """Get configuration from environment variables"""
        env_config = {}
        
        # LLM configuration
        if os.getenv('OPENAI_API_KEY'):
            env_config['llm'] = {
                'provider': 'openai',
                'api_key': os.getenv('OPENAI_API_KEY'),
                'model': os.getenv('OPENAI_MODEL', 'gpt-4')
            }
        
        # API keys
        api_keys = {}
        for key in ['COINGECKO_API_KEY', 'BINANCE_API_KEY', 'GLASSNODE_API_KEY']:
            if os.getenv(key):
                api_keys[key] = os.getenv(key)
        
        if api_keys:
            env_config['api_keys'] = api_keys
        
        return env_config
```

### 4. Web Interface Architecture

#### Streamlit Component Architecture
```python
import streamlit as st
from typing import Dict, Any, Optional, Callable
import asyncio

class BaseStreamlitComponent:
    """Base class for Streamlit components"""
    
    def __init__(self, component_id: str):
        self.component_id = component_id
        self.session_state_key = f"{component_id}_state"
    
    def get_state(self) -> Dict[str, Any]:
        """Get component state from session state"""
        return st.session_state.get(self.session_state_key, {})
    
    def set_state(self, state: Dict[str, Any]):
        """Set component state in session state"""
        st.session_state[self.session_state_key] = state
    
    def render(self) -> Any:
        """Render the component - to be implemented by subclasses"""
        raise NotImplementedError

class AnalysisFormComponent(BaseStreamlitComponent):
    """Analysis form component"""
    
    def render(self) -> Dict[str, Any]:
        """Render analysis form"""
        with st.form("analysis_form"):
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
                index=0
            )
            
            # Analysis level
            analysis_level = st.slider(
                "分析级别",
                min_value=1,
                max_value=5,
                value=3,
                step=1
            )
            
            # Agent selection
            agents = st.multiselect(
                "分析代理",
                options=["technical", "onchain", "sentiment", "defi", "market_maker"],
                default=["technical", "sentiment"]
            )
            
            # Submit button
            submitted = st.form_submit_button("开始分析")
            
            if submitted:
                return {
                    'submitted': True,
                    'symbol': symbol.upper(),
                    'exchange': exchange,
                    'analysis_level': analysis_level,
                    'agents': agents
                }
        
        return {'submitted': False}

class ProgressDisplayComponent(BaseStreamlitComponent):
    """Progress display component"""
    
    def render(self, analysis_id: str) -> bool:
        """Render progress display for analysis"""
        progress_tracker = AsyncProgressTracker(analysis_id)
        progress_data = progress_tracker.get_progress()
        
        if not progress_data:
            st.warning("No progress data available")
            return False
        
        # Progress bar
        progress = progress_data.get('progress', 0)
        st.progress(progress / 100)
        
        # Status message
        status = progress_data.get('status', 'unknown')
        if status == 'completed':
            st.success("✅ Analysis completed!")
            return True
        elif status == 'failed':
            st.error("❌ Analysis failed")
            return True
        else:
            st.info(f"🔄 {progress_data.get('message', 'In progress...')}")
            return False
```

### 5. Asynchronous Processing Architecture

#### Async Task Management
```python
import asyncio
import threading
from typing import Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
import uuid
from datetime import datetime

class AsyncTaskManager:
    """Manages asynchronous tasks with thread safety"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, Any] = {}
        self.lock = threading.Lock()
    
    async def submit_task(self, func: Callable, *args, **kwargs) -> str:
        """Submit a task for asynchronous execution"""
        task_id = str(uuid.uuid4())
        
        async def task_wrapper():
            try:
                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.executor, func, *args, **kwargs
                )
                
                with self.lock:
                    self.task_results[task_id] = {
                        'status': 'completed',
                        'result': result,
                        'completed_at': datetime.now().isoformat()
                    }
                
                return result
            
            except Exception as e:
                with self.lock:
                    self.task_results[task_id] = {
                        'status': 'failed',
                        'error': str(e),
                        'failed_at': datetime.now().isoformat()
                    }
                raise
        
        # Create and start task
        task = asyncio.create_task(task_wrapper())
        
        with self.lock:
            self.active_tasks[task_id] = task
        
        return task_id
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result"""
        with self.lock:
            return self.task_results.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        with self.lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.cancel()
                del self.active_tasks[task_id]
                
                self.task_results[task_id] = {
                    'status': 'cancelled',
                    'cancelled_at': datetime.now().isoformat()
                }
                
                return True
        return False
    
    def cleanup_completed_tasks(self):
        """Clean up completed tasks older than 1 hour"""
        cutoff_time = datetime.now().timestamp() - 3600  # 1 hour ago
        
        with self.lock:
            to_remove = []
            for task_id, result in self.task_results.items():
                if result['status'] in ['completed', 'failed']:
                    completed_at = datetime.fromisoformat(result.get('completed_at', result.get('failed_at', '2024-01-01')))
                    if completed_at.timestamp() < cutoff_time:
                        to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.task_results[task_id]

class AsyncProgressTracker:
    """Tracks progress of asynchronous operations"""
    
    def __init__(self, analysis_id: str):
        self.analysis_id = analysis_id
        self.progress_file = f"~/.crypto_trading_agents/progress/{analysis_id}.json"
        self.lock = threading.Lock()
    
    def update_progress(self, step: int, message: str, progress: float):
        """Update progress with thread safety"""
        with self.lock:
            progress_data = {
                'analysis_id': self.analysis_id,
                'step': step,
                'message': message,
                'progress': progress,
                'timestamp': datetime.now().isoformat(),
                'status': 'running'
            }
            self._save_progress(progress_data)
    
    def mark_completed(self, message: str, results: Optional[Dict[str, Any]] = None):
        """Mark analysis as completed"""
        with self.lock:
            progress_data = {
                'analysis_id': self.analysis_id,
                'message': message,
                'progress': 100.0,
                'timestamp': datetime.now().isoformat(),
                'status': 'completed'
            }
            if results:
                progress_data['raw_results'] = results
            self._save_progress(progress_data)
    
    def mark_failed(self, error_message: str):
        """Mark analysis as failed"""
        with self.lock:
            progress_data = {
                'analysis_id': self.analysis_id,
                'message': error_message,
                'progress': 0.0,
                'timestamp': datetime.now().isoformat(),
                'status': 'failed'
            }
            self._save_progress(progress_data)
    
    def _save_progress(self, progress_data: Dict[str, Any]):
        """Save progress data to file"""
        try:
            os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
    
    def get_progress(self) -> Optional[Dict[str, Any]]:
        """Get current progress data"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load progress: {e}")
        return None
```

### 6. Database Architecture

#### Data Models
```python
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from enum import Enum

class AnalysisStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AnalysisResult:
    """Analysis result data model"""
    analysis_id: str
    timestamp: str
    symbol: str
    exchange: str
    analysis_type: str
    analysis_level: int
    agents_used: List[str]
    results: Dict[str, Any]
    trading_signals: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    confidence_score: float
    status: AnalysisStatus
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """Create from dictionary"""
        data['status'] = AnalysisStatus(data['status'])
        return cls(**data)

@dataclass
class SessionData:
    """User session data model"""
    session_id: str
    user_id: str
    created_at: str
    last_accessed: str
    analysis_history: List[str]
    preferences: Dict[str, Any]
    current_analysis: Optional[str] = None
    cache: Optional[Dict[str, Any]] = None
    
    def update_access_time(self):
        """Update last accessed time"""
        self.last_accessed = datetime.now().isoformat()

class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self, base_path: str = "~/.crypto_trading_agents"):
        self.base_path = Path(base_path)
        self.data_path = self.base_path / "data"
        self.analysis_path = self.data_path / "analysis"
        self.sessions_path = self.data_path / "sessions"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all necessary directories exist"""
        for path in [self.data_path, self.analysis_path, self.sessions_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def save_analysis_result(self, result: AnalysisResult) -> bool:
        """Save analysis result to database"""
        try:
            file_path = self.analysis_path / f"{result.analysis_id}.json"
            with open(file_path, 'w') as f:
                json.dump(result.to_dict(), f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save analysis result: {e}")
            return False
    
    def load_analysis_result(self, analysis_id: str) -> Optional[AnalysisResult]:
        """Load analysis result from database"""
        try:
            file_path = self.analysis_path / f"{analysis_id}.json"
            if not file_path.exists():
                return None
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            return AnalysisResult.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load analysis result: {e}")
            return None
    
    def get_recent_analyses(self, limit: int = 10) -> List[AnalysisResult]:
        """Get recent analysis results"""
        try:
            analysis_files = list(self.analysis_path.glob("*.json"))
            analysis_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            results = []
            for file_path in analysis_files[:limit]:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    results.append(AnalysisResult.from_dict(data))
                except Exception as e:
                    logger.error(f"Failed to load analysis from {file_path}: {e}")
            
            return results
        except Exception as e:
            logger.error(f"Failed to get recent analyses: {e}")
            return []
    
    def cleanup_old_data(self, max_age_hours: int = 48):
        """Clean up old data files"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        # Clean up analysis results
        for file_path in self.analysis_path.glob("*.json"):
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
        
        # Clean up session data
        for file_path in self.sessions_path.glob("*.json"):
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
```

### 7. Security Architecture

#### Security Layers
```
┌─────────────────────────────────────────────────────────────┐
│                    Application Security                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ Input   │ │ Session │ │ Rate    │ │ Error   │          │
│  │ Validation│ │ Mgmt   │ │ Limiting│ │ Handling│          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Data Security                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ API Key │ │ Data    │ │ Cache   │ │ Audit   │          │
│  │ Encryption│ │ Encryption│ │ Security│ │ Logging │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Security                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │ Network │ │ Server  │ │ Container│ │ Monitoring│          │
│  │ Security│ │ Security│ │ Security│ │ & Alerting│          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 8. Performance Architecture

#### Performance Optimization Strategies
```python
import asyncio
import time
from typing import Dict, Any, List, Optional
from functools import wraps
import cachetools
from concurrent.futures import ThreadPoolExecutor

class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    def __init__(self):
        self.cache = cachetools.TTLCache(maxsize=1000, ttl=300)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.metrics = {}
    
    def cached(self, ttl: int = 300):
        """Caching decorator with TTL"""
        def decorator(func):
            @cachetools.cached(cache=self.cache)
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    async def batch_process(self, items: List[Any], processor: Callable, batch_size: int = 10) -> List[Any]:
        """Process items in batches for better performance"""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await asyncio.gather(*[
                self._run_in_executor(processor, item) for item in batch
            ])
            results.extend(batch_results)
        
        return results
    
    async def _run_in_executor(self, func: Callable, *args) -> Any:
        """Run function in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args)
    
    def record_metric(self, name: str, value: float, metadata: Optional[Dict[str, Any]] = None):
        """Record performance metric"""
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            'value': value,
            'timestamp': time.time(),
            'metadata': metadata or {}
        })
    
    def get_metrics_summary(self, name: str) -> Dict[str, float]:
        """Get summary statistics for a metric"""
        if name not in self.metrics or not self.metrics[name]:
            return {}
        
        values = [m['value'] for m in self.metrics[name]]
        return {
            'count': len(values),
            'mean': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'latest': values[-1]
        }
```

## Integration Patterns

### 1. Agent Integration Pattern
```python
class AgentIntegrationPattern:
    """Pattern for integrating multiple agents"""
    
    def __init__(self):
        self.agents = {}
        self.message_bus = MessageBus()
        self.result_store = ResultStore()
    
    def register_agent(self, agent_type: str, agent: BaseAgent):
        """Register an agent"""
        self.agents[agent_type] = agent
    
    async def coordinate_analysis(self, request: AnalysisRequest) -> AnalysisResult:
        """Coordinate analysis across multiple agents"""
        # Step 1: Route request to appropriate agents
        selected_agents = self._select_agents(request)
        
        # Step 2: Execute analysis in parallel
        tasks = [agent.analyze(request.data) for agent in selected_agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Step 3: Synthesize results
        synthesized_result = await self._synthesize_results(results)
        
        # Step 4: Store result
        await self.result_store.store(request.analysis_id, synthesized_result)
        
        return synthesized_result
```

### 2. Data Integration Pattern
```python
class DataIntegrationPattern:
    """Pattern for integrating multiple data sources"""
    
    def __init__(self):
        self.sources = {}
        self.normalizer = DataNormalizer()
        self.validator = DataValidator()
    
    def register_source(self, source_type: str, source: BaseDataSource):
        """Register a data source"""
        self.sources[source_type] = source
    
    async def get_integrated_data(self, symbol: str) -> Dict[str, Any]:
        """Get integrated data from multiple sources"""
        # Fetch data from multiple sources in parallel
        tasks = [
            source.fetch_data(symbol) 
            for source in self.sources.values()
        ]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_results = [
            result for result in raw_results 
            if not isinstance(result, Exception)
        ]
        
        # Normalize and validate data
        normalized_data = self.normalizer.normalize(successful_results)
        validated_data = self.validator.validate(normalized_data)
        
        return validated_data
```

## Deployment Architecture

### Container Architecture
```dockerfile
# Multi-stage Docker build
FROM python:3.10-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.10-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Create app user
RUN useradd -m -u 1000 appuser
WORKDIR /app
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/cache && \
    chown -R appuser:appuser /app

# Switch to app user
USER appuser

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Start application
CMD ["streamlit", "run", "web/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Microservices Architecture (Future)
```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway                                │
└─────────────────────────────────────────────────────────────┘
                              │
    ┌───────────────────┼───────────────────┐
    │                   │                   │
┌───────┐         ┌───────┐         ┌───────┐         ┌───────┐
│ Agent │         │ Data  │         │ Web   │         │ Auth  │
│Service│         │Service│         │Service│         │Service│
└───────┘         └───────┘         └───────┘         └───────┘
    │                   │                   │                   │
    └───────────────────┼───────────────────┼───────────────────┘
                        │                   │
                ┌───────┐         ┌───────┐         ┌───────┐
                │Redis  │         │MongoDB│         │Monitor│
                │Cache  │         │Database│         │Service│
                └───────┘         └───────┘         └───────┘
```

This architecture provides a solid foundation for building scalable, maintainable, and secure cryptocurrency trading analysis system with multiple AI agents working in collaboration.