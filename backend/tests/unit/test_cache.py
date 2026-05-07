import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.cache import _make_key, get_cached, set_cached


# --- _make_key ---

def test_make_key_format():
    key = _make_key("questions", topic="Python", count=5)
    assert key.startswith("ai:questions:")
    assert len(key) == len("ai:questions:") + 16


def test_make_key_deterministic():
    k1 = _make_key("questions", topic="Python", count=5)
    k2 = _make_key("questions", topic="Python", count=5)
    assert k1 == k2


def test_make_key_different_params_produce_different_keys():
    k1 = _make_key("questions", topic="Python")
    k2 = _make_key("questions", topic="Java")
    assert k1 != k2


def test_make_key_order_independent():
    k1 = _make_key("x", a=1, b=2)
    k2 = _make_key("x", b=2, a=1)
    assert k1 == k2


def test_make_key_different_prefixes():
    k1 = _make_key("questions", topic="Python")
    k2 = _make_key("flashcards", topic="Python")
    assert k1 != k2


# --- get_cached / set_cached with use_cache=False ---

async def test_get_cached_returns_none_when_disabled():
    with patch("app.services.cache.settings") as mock_settings:
        mock_settings.use_cache = False
        result = await get_cached("questions", topic="Python")
    assert result is None


async def test_set_cached_is_noop_when_disabled():
    with patch("app.services.cache.settings") as mock_settings:
        mock_settings.use_cache = False
        # Should complete without touching Redis
        await set_cached("questions", {"data": "value"}, topic="Python")


# --- get_cached / set_cached with mocked Redis ---

async def test_get_cached_hit():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=json.dumps({"answer": 42}))

    with patch("app.services.cache.settings") as mock_settings, \
         patch("app.services.cache.get_redis", return_value=mock_redis):
        mock_settings.use_cache = True
        result = await get_cached("q", topic="test")

    assert result == {"answer": 42}


async def test_get_cached_miss_returns_none():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)

    with patch("app.services.cache.settings") as mock_settings, \
         patch("app.services.cache.get_redis", return_value=mock_redis):
        mock_settings.use_cache = True
        result = await get_cached("q", topic="test")

    assert result is None


async def test_get_cached_redis_error_returns_none():
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(side_effect=ConnectionError("redis down"))

    with patch("app.services.cache.settings") as mock_settings, \
         patch("app.services.cache.get_redis", return_value=mock_redis):
        mock_settings.use_cache = True
        result = await get_cached("q", topic="test")

    assert result is None


async def test_set_cached_stores_json():
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()

    with patch("app.services.cache.settings") as mock_settings, \
         patch("app.services.cache.get_redis", return_value=mock_redis):
        mock_settings.use_cache = True
        mock_settings.cache_ttl = 3600
        await set_cached("q", {"key": "val"}, topic="test")

    mock_redis.set.assert_awaited_once()
    args = mock_redis.set.call_args
    stored_value = args[0][1]
    assert json.loads(stored_value) == {"key": "val"}


async def test_set_cached_redis_error_is_swallowed():
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock(side_effect=ConnectionError("redis down"))

    with patch("app.services.cache.settings") as mock_settings, \
         patch("app.services.cache.get_redis", return_value=mock_redis):
        mock_settings.use_cache = True
        mock_settings.cache_ttl = 3600
        await set_cached("q", {"key": "val"}, topic="test")  # no raise


async def test_set_cached_uses_custom_ttl():
    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()

    with patch("app.services.cache.settings") as mock_settings, \
         patch("app.services.cache.get_redis", return_value=mock_redis):
        mock_settings.use_cache = True
        mock_settings.cache_ttl = 3600
        await set_cached("q", "data", ttl=120, topic="test")

    _, kwargs = mock_redis.set.call_args
    assert kwargs.get("ex") == 120