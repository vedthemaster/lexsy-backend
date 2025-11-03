from fastapi import APIRouter

from .document import document_router
from .placeholder import placeholder_router


router = APIRouter()
router.include_router(document_router, prefix="/documents")
router.include_router(placeholder_router, prefix="/placeholders")

__all__ = ["router"]