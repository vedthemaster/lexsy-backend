from fastapi import APIRouter

from .document import document_router

router = APIRouter()
router.include_router(document_router, prefix="/documents")

__all__ = ["router"]