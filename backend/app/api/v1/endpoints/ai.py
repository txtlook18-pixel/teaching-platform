from fastapi import APIRouter
from app.providers.factory import get_ai_provider
from app.config import settings

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/health")
async def ai_health():
    ai = get_ai_provider()
    is_healthy = await ai.health_check()
    return {
        "status": "ok" if is_healthy else "error",
        "mode": settings.ai_mode,
        "provider": settings.ai_provider,
        "healthy": is_healthy,
    }
