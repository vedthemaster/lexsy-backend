from fastapi import (
    APIRouter,
    HTTPException,
    status,
    UploadFile,
    File,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel

# TODO: Import v2 services once implemented
# from services.document_service_v2 import document_service_v2
# from services.document_generator_service_v2 import document_generator_service_v2

document_router = APIRouter()


class GenerateDocumentRequest(BaseModel):
    document_id: str


@document_router.get("/", status_code=200)
async def health():
    return {"message": "API v2 is running (LangChain-based)"}


@document_router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process document using LangChain approach
    TODO: Implement v2 logic
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="V2 upload endpoint not yet implemented",
    )


@document_router.post("/generate")
async def generate_document(request: GenerateDocumentRequest):
    """
    Generate a filled document using LangChain approach
    TODO: Implement v2 logic
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="V2 generate endpoint not yet implemented",
    )
