from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    HTTPException,
    status,
    UploadFile,
    Request,
    File,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel

from models import Document
from services.document_service import document_service
from services.document_generator_service import document_generator_service

document_router = APIRouter()


class GenerateDocumentRequest(BaseModel):
    document_id: str


@document_router.get("/", status_code=200)
async def health():
    return {"message": "API is running"}


@document_router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)):
    document = await document_service.upload_and_process_document(file)
    return {"message": "Document uploaded successfully", "document_id": str(document.id), "title": document.title}


@document_router.post("/generate")
async def generate_document(request: GenerateDocumentRequest):
    """
    Generate a filled document and return as downloadable file
    """
    try:
        result = await document_generator_service.generate_filled_document(
            request.document_id
        )

        return FileResponse(
            path=result["output_path"],
            filename=result["output_filename"],
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating document: {str(e)}",
        )
