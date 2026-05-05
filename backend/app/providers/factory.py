from app.config import settings, AIMode, AIProviderType
from .base import BaseAIProvider
from .api_provider import APIProvider
from .local_provider import LocalProvider

_provider_instance: BaseAIProvider = None


def get_ai_provider() -> BaseAIProvider:
    global _provider_instance
    if _provider_instance is None:
        if settings.ai_mode == AIMode.LOCAL:
            _provider_instance = LocalProvider()
        else:
            _provider_instance = APIProvider()
    return _provider_instance
