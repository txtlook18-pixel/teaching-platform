"""Unit tests for AI provider factory, base class, and AI health endpoint."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# --- factory ---

def test_factory_returns_api_provider_by_default():
    """Reset singleton and check API mode."""
    import app.providers.factory as factory_module
    original = factory_module._provider_instance
    factory_module._provider_instance = None
    try:
        with patch("app.providers.factory.settings") as mock_settings:
            from app.config import AIMode
            mock_settings.ai_mode = AIMode.API
            provider = factory_module.get_ai_provider()
            from app.providers.api_provider import APIProvider
            assert isinstance(provider, APIProvider)
    finally:
        factory_module._provider_instance = original


def test_factory_returns_local_provider_in_local_mode():
    import app.providers.factory as factory_module
    original = factory_module._provider_instance
    factory_module._provider_instance = None
    try:
        with patch("app.providers.factory.settings") as mock_settings:
            from app.config import AIMode
            mock_settings.ai_mode = AIMode.LOCAL
            provider = factory_module.get_ai_provider()
            from app.providers.local_provider import LocalProvider
            assert isinstance(provider, LocalProvider)
    finally:
        factory_module._provider_instance = original


def test_factory_caches_singleton():
    """Calling get_ai_provider twice returns the same instance."""
    import app.providers.factory as factory_module
    original = factory_module._provider_instance
    factory_module._provider_instance = None
    try:
        with patch("app.providers.factory.settings") as mock_settings:
            from app.config import AIMode
            mock_settings.ai_mode = AIMode.API
            p1 = factory_module.get_ai_provider()
            p2 = factory_module.get_ai_provider()
            assert p1 is p2
    finally:
        factory_module._provider_instance = original


# --- base provider abstract methods ---

def test_base_provider_is_abstract():
    """BaseAIProvider cannot be instantiated directly."""
    import inspect
    from app.providers.base import BaseAIProvider
    assert inspect.isabstract(BaseAIProvider)


def test_base_provider_subclass_without_methods_raises():
    from app.providers.base import BaseAIProvider

    class Incomplete(BaseAIProvider):
        pass

    with pytest.raises(TypeError):
        Incomplete()


# --- ai health endpoint ---

async def test_ai_health_ok(client):
    with patch("app.api.v1.endpoints.ai.get_ai_provider") as mock_factory:
        mock_ai = AsyncMock()
        mock_ai.health_check = AsyncMock(return_value=True)
        mock_factory.return_value = mock_ai
        r = await client.get("/api/v1/ai/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["healthy"] is True


async def test_ai_health_error(client):
    with patch("app.api.v1.endpoints.ai.get_ai_provider") as mock_factory:
        mock_ai = AsyncMock()
        mock_ai.health_check = AsyncMock(return_value=False)
        mock_factory.return_value = mock_ai
        r = await client.get("/api/v1/ai/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "error"
    assert data["healthy"] is False
