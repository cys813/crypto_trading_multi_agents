from .base_adapter import BaseNewsAdapter
from .coindesk_adapter import CoinDeskAdapter
from .cointelegraph_adapter import CoinTelegraphAdapter
from .decrypt_adapter import DecryptAdapter

__all__ = [
    "BaseNewsAdapter",
    "CoinDeskAdapter",
    "CoinTelegraphAdapter",
    "DecryptAdapter",
]