"""
智能做空信号识别系统模块

该模块实现了多种信号融合算法，包括：
1. 加权求和融合
2. 共识投票融合
3. 分层融合
4. 信号强度评估
5. 置信度计算
6. 风险评估
"""

from .intelligent_signal_recognition import (
    IntelligentSignalRecognition,
    SignalFusionMethod,
    SignalFusionConfig,
    FusionSignal,
    SignalComponent
)

__all__ = [
    'IntelligentSignalRecognition',
    'SignalFusionMethod',
    'SignalFusionConfig',
    'FusionSignal',
    'SignalComponent'
]