from fastapi import APIRouter

from .v1 import router as v1_router
from .v2 import router as v2_router


router = APIRouter()

# Include v1 routes (current OpenAI function calling approach)
router.include_router(v1_router, prefix="/v1", tags=["v1"])

# Include v2 routes (LangChain-based approach)
router.include_router(v2_router, prefix="/v2", tags=["v2"])

__all__ = ["router"]
