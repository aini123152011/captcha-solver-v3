"""接口模块"""

from .ai_provider import AIProviderType, IAIProvider, IAIProviderManager, ImageAnalysisResult
from .browser import IBrowserPool, ICaptchaSolver, SolveResult
from .repositories import ITaskRepository, ITransactionRepository, IUserRepository

__all__ = [
    "IUserRepository",
    "ITaskRepository", 
    "ITransactionRepository",
    "IAIProvider",
    "IAIProviderManager",
    "AIProviderType",
    "ImageAnalysisResult",
    "IBrowserPool",
    "ICaptchaSolver",
    "SolveResult",
]
