---
name: 做空技术指标引擎
epic: 做空分析师代理
task_id: 043-short-indicators
status: pending
priority: P1
estimated_hours: 56
parallel: true
dependencies: ["041-architecture-design", "042-data-receiver"]
github_issue: https://github.com/cys813/crypto_trading_multi_agents/issues/43
---

# Task: 做空技术指标引擎

## Task Description
实现专门针对做空信号的技术指标引擎，包括趋势反转指标、超买指标、压力位指标、成交量指标和市场情绪指标。建立做空专用指标库，优化信号识别算法，提供高质量的做空信号输入。

## Acceptance Criteria

### 做空指标实现
- [ ] 完成趋势反转指标集（MA交叉、MACD顶背离、RSI超买等）
- [ ] 实现压力位指标（布林带上轨、历史阻力位、斐波那契阻力位）
- [ ] 建立成交量指标（下跌放量、量价背离、OBV背离）
- [ ] 完成市场情绪指标（恐惧贪婪指数、负面情绪指标）
- [ ] 实现顶部形态识别（头肩顶、双顶、圆弧顶等）

### 指标优化与验证
- [ ] 指标参数优化和自适应调整
- [ ] 多时间框架指标整合
- [ ] 指标历史回测和验证
- [ ] 指标信号强度评分系统
- [ ] 指标性能监控和调优

### 性能与准确性
- [ ] 指标计算延迟 < 200ms
- [ ] 指标准确率 > 70%
- [ ] 支持并发指标计算
- [ ] 内存使用优化
- [ ] 实现指标计算缓存

## Technical Implementation Details

### 核心指标引擎设计
1. **ShortIndicatorEngine (做空指标引擎)**
   ```python
   class ShortIndicatorEngine:
       def __init__(self, config: IndicatorConfig):
           self.config = config
           self.trend_indicators = TrendIndicators(config.trend_config)
           self.momentum_indicators = MomentumIndicators(config.momentum_config)
           self.volume_indicators = VolumeIndicators(config.volume_config)
           self.pattern_indicators = PatternIndicators(config.pattern_config)
           self.sentiment_indicators = SentimentIndicators(config.sentiment_config)
           self.cache = IndicatorCache(config.cache_config)

       async def calculate_short_signals(self, data: MarketData) -> ShortSignalSet:
           # 计算做空信号集合
           trend_signals = await self.trend_indicators.calculate_reversal_signals(data)
           momentum_signals = await self.momentum_indicators.calculate_overbought_signals(data)
           volume_signals = await self.volume_indicators.calculate_distribution_signals(data)
           pattern_signals = await self.pattern_indicators.calculate_top_patterns(data)
           sentiment_signals = await self.sentiment_indicators.calculate_fear_signals(data)

           return ShortSignalSet(
               trend_signals=trend_signals,
               momentum_signals=momentum_signals,
               volume_signals=volume_signals,
               pattern_signals=pattern_signals,
               sentiment_signals=sentiment_signals,
               combined_signal=self.combine_signals(trend_signals, momentum_signals, volume_signals, pattern_signals, sentiment_signals)
           )
   ```

2. **趋势反转指标**
   ```python
   class TrendReversalIndicators:
       def calculate_ma_cross_signals(self, data: PriceData) -> List[Signal]:
           # 移动平均线交叉信号（死亡交叉）
           ma_short = self.calculate_ma(data.prices, config.ma_short_period)
           ma_long = self.calculate_ma(data.prices, config.ma_long_period)

           if ma_short[-1] < ma_long[-1] and ma_short[-2] >= ma_long[-2]:
               return [Signal(
                   type="death_cross",
                   strength=self.calculate_ma_cross_strength(ma_short, ma_long),
                   timestamp=data.timestamp,
                   price=data.current_price
               )]
           return []

       def calculate_macd_divergence(self, data: PriceData) -> List[Signal]:
           # MACD顶背离信号
           macd_line, signal_line, histogram = self.calculate_macd(data.prices)

           # 检测顶背离：价格创新高但MACD未创新高
           if self.detect_price_high(data.prices) and not self.detect_macd_high(macd_line):
               return [Signal(
                   type="macd_bearish_divergence",
                   strength=self.calculate_divergence_strength(data.prices, macd_line),
                   timestamp=data.timestamp,
                   price=data.current_price
               )]
           return []

       def calculate_rsi_overbought(self, data: PriceData) -> List[Signal]:
           # RSI超买信号
           rsi = self.calculate_rsi(data.prices, config.rsi_period)

           if rsi[-1] > config.rsi_overbought_threshold:
               return [Signal(
                   type="rsi_overbought",
                   strength=self.calculate_rsi_strength(rsi),
                   timestamp=data.timestamp,
                   price=data.current_price
               )]
           return []
   ```

3. **压力位指标**
   ```python
   class ResistanceIndicators:
       def calculate_bollinger_upper_breakout(self, data: PriceData) -> List[Signal]:
           # 布林带上轨突破信号
           bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(data.prices)

           if data.current_price > bb_upper[-1]:
               return [Signal(
                   type="bollinger_upper_breakout",
                   strength=self.calculate_bollinger_breakout_strength(data.current_price, bb_upper[-1]),
                   timestamp=data.timestamp,
                   price=data.current_price
               )]
           return []

       def calculate_resistance_levels(self, data: PriceData) -> List[Signal]:
           # 历史阻力位信号
           resistance_levels = self.find_resistance_levels(data.prices)

           for level in resistance_levels:
               if abs(data.current_price - level) / level < config.resistance_threshold:
                   return [Signal(
                       type="resistance_level",
                       strength=self.calculate_resistance_strength(data.prices, level),
                       timestamp=data.timestamp,
                       price=data.current_price,
                       resistance_level=level
                   )]
           return []

       def calculate_fibonacci_resistance(self, data: PriceData) -> List[Signal]:
           # 斐波那契阻力位信号
           high_price = max(data.prices[-config.fibonacci_period:])
           low_price = min(data.prices[-config.fibonacci_period:])

           resistance_levels = self.calculate_fibonacci_levels(high_price, low_price)

           for level in resistance_levels:
               if abs(data.current_price - level) / level < config.fibonacci_threshold:
                   return [Signal(
                       type="fibonacci_resistance",
                       strength=self.calculate_fibonacci_strength(data.current_price, level),
                       timestamp=data.timestamp,
                       price=data.current_price,
                       fibonacci_level=level
                   )]
           return []
   ```

4. **成交量指标**
   ```python
   class VolumeIndicators:
       def calculate_distribution_volume(self, data: MarketData) -> List[Signal]:
           # 下跌放量信号（出货信号）
           avg_volume = self.calculate_avg_volume(data.volumes, config.volume_ma_period)
           current_volume = data.volumes[-1]

           if current_volume > avg_volume * config.volume_spike_multiplier and data.price_change < 0:
               return [Signal(
                   type="distribution_volume",
                   strength=self.calculate_distribution_strength(current_volume, avg_volume),
                   timestamp=data.timestamp,
                   price=data.current_price,
                   volume_ratio=current_volume / avg_volume
               )]
           return []

       def calculate_volume_price_divergence(self, data: MarketData) -> List[Signal]:
           # 量价背离信号
           price_trend = self.calculate_price_trend(data.prices)
           volume_trend = self.calculate_volume_trend(data.volumes)

           # 价格上涨但成交量下降（顶背离）
           if price_trend > 0 and volume_trend < 0:
               return [Signal(
                   type="volume_price_bearish_divergence",
                   strength=self.calculate_divergence_strength(price_trend, volume_trend),
                   timestamp=data.timestamp,
                   price=data.current_price
               )]
           return []

       def calculate_obv_divergence(self, data: MarketData) -> List[Signal]:
           # OBV背离信号
           obv = self.calculate_obv(data.prices, data.volumes)
           obv_trend = self.calculate_trend(obv[-config.trend_period:])
           price_trend = self.calculate_trend(data.prices[-config.trend_period:])

           # 价格上涨但OBV下降
           if price_trend > 0 and obv_trend < 0:
               return [Signal(
                   type="obv_bearish_divergence",
                   strength=self.calculate_obv_divergence_strength(obv_trend, price_trend),
                   timestamp=data.timestamp,
                   price=data.current_price
               )]
           return []
   ```

5. **顶部形态识别**
   ```python
   class PatternRecognition:
       def detect_head_shoulders_top(self, data: PriceData) -> List[Signal]:
           # 头肩顶形态识别
           pattern = self.identify_head_shoulders_pattern(data.prices)

           if pattern and pattern.confidence > config.pattern_threshold:
               return [Signal(
                   type="head_shoulders_top",
                   strength=pattern.confidence,
                   timestamp=data.timestamp,
                   price=data.current_price,
                   pattern_data=pattern
               )]
           return []

       def detect_double_top(self, data: PriceData) -> List[Signal]:
           # 双顶形态识别
           pattern = self.identify_double_top_pattern(data.prices)

           if pattern and pattern.confidence > config.pattern_threshold:
               return [Signal(
                   type="double_top",
                   strength=pattern.confidence,
                   timestamp=data.timestamp,
                   price=data.current_price,
                   pattern_data=pattern
               )]
           return []

       def detect_rounding_top(self, data: PriceData) -> List[Signal]:
           # 圆弧顶形态识别
           pattern = self.identify_rounding_top_pattern(data.prices)

           if pattern and pattern.confidence > config.pattern_threshold:
               return [Signal(
                   type="rounding_top",
                   strength=pattern.confidence,
                   timestamp=data.timestamp,
                   price=data.current_price,
                   pattern_data=pattern
               )]
           return []
   ```

### 指标信号整合与评分
1. **信号强度计算**
   ```python
   def calculate_signal_strength(self, signals: List[Signal]) -> float:
       # 计算综合信号强度
       total_strength = 0
       weight_sum = 0

       for signal in signals:
           weight = self.get_signal_weight(signal.type)
           total_strength += signal.strength * weight
           weight_sum += weight

       return total_strength / weight_sum if weight_sum > 0 else 0

   def combine_signals(self, *signal_groups) -> CombinedSignal:
       # 整合多组信号
       all_signals = []
       for group in signal_groups:
           all_signals.extend(group)

       # 信号过滤和去重
       filtered_signals = self.filter_and_deduplicate_signals(all_signals)

       # 计算综合评分
       strength = self.calculate_signal_strength(filtered_signals)
       confidence = self.calculate_signal_confidence(filtered_signals)

       return CombinedSignal(
           signals=filtered_signals,
           strength=strength,
           confidence=confidence,
           timestamp=datetime.now(),
           recommendation=self.generate_recommendation(strength, confidence)
       )
   ```

### 技术实现要点
- **做空专用**: 所有指标专门针对做空信号优化
- **多时间框架**: 支持多个时间框架的指标分析
- **实时计算**: 优化的实时指标计算算法
- **信号整合**: 智能信号整合和去重机制
- **自适应调整**: 根据市场条件自动调整指标参数

## Deliverables

1. **做空指标引擎**
   - ShortIndicatorEngine 主类实现
   - 5大类型做空指标实现
   - 信号强度评估系统

2. **技术指标库**
   - 趋势反转指标集
   - 压力位指标集
   - 成交量指标集
   - 形态识别算法
   - 市场情绪指标

3. **信号处理系统**
   - 信号过滤和整合
   - 强度评分算法
   - 置信度计算
   - 历史验证系统

4. **测试与优化**
   - 指标准确性测试
   - 性能优化报告
   - 参数调优指南
   - 使用文档

## Dependencies
- 040-architecture-design (架构设计完成)
- 041-data-receiver (数据接收模块)
- 技术指标计算库依赖

## Risks and Mitigation

### 技术风险
- **指标计算性能**: 大量指标计算可能影响系统性能
  - 缓解: 实现并行计算和缓存机制
- **信号准确性**: 做空信号识别准确性不足
  - 缓解: 多指标组合和历史数据验证

### 业务风险
- **市场适应性**: 指标在不同市场环境下表现差异
  - 缓解: 实现自适应参数调整机制
- **过度拟合**: 指标参数过度拟合历史数据
  - 缓解: 使用交叉验证和样本外测试

## Success Metrics
- 指标计算延迟: <200ms
- 做空信号准确率: >70%
- 信号整合评分准确性: >75%
- 系统资源使用: 内存<256MB
- 指标缓存命中率: >85%
- 并发处理能力: 支持100+并发请求

## Notes
- 重点关注做空特有的技术指标和信号
- 确保指标计算的实时性和准确性
- 建立完善的信号验证和评分机制
- 为LLM分析提供高质量的输入数据