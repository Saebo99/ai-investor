"""
Data acquisition interfaces for market and portfolio information.
"""

from .eodhd import EODHDClient
from .nordnet import NordnetClient

__all__ = ["EODHDClient", "NordnetClient"]
