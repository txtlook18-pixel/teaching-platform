from fastapi import APIRouter
from sqlalchemy import text

from app.db.database import engine
from app.services.cache import get_redis

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health():
    """Проверка состояния всех компонентов системы."""
    db_status = "ok"
    redis_status = "ok"

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    try:
        r = await get_redis()
        await r.ping()
    except Exception as e:
        redis_status = f"error: {str(e)}"

    overall = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"

    return {
        "status": overall,
        "components": {
            "database": db_status,
            "redis": redis_status,
        },
        "version": "1.0.0",
    }
