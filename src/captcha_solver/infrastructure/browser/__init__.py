"""浏览器模块"""

from .pool import BrowserPoolV2, close_browser_pool, get_browser_pool
from .solver import RecaptchaV2Solver, WhisperTranscriber

__all__ = [
    "BrowserPoolV2",
    "get_browser_pool",
    "close_browser_pool",
    "RecaptchaV2Solver",
    "WhisperTranscriber",
]
