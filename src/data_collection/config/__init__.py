"""
Configuration module for data collection agent.

This module contains configuration settings and environment variables
for the data collection system.
"""

from .settings import Settings, get_settings

__all__ = [
    "Settings",
    "get_settings"
]