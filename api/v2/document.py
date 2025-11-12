from fastapi import (
    APIRouter,
    HTTPException,
    status,
    UploadFile,
    File,
)
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from api.v2.services import document_service, document_generator_service

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
    - Uses multi-stage pipeline with custom tools
    - Provides enhanced placeholder analysis
    """
    try:
        if not file.filename.endswith(".docx"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .docx files are supported",
            )

        document = await document_service.upload_and_parse(file)

        return {
            "message": "Document uploaded and analyzed successfully with LangChain",
            "document_id": str(document.id),
            "title": document.title,
            "placeholders": [p.model_dump() for p in document.placeholders],
            "analysis_metadata": document.analysis_metadata,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )


@document_router.post("/generate")
async def generate_document(request: GenerateDocumentRequest):
    """
    Generate a filled document using LangChain approach
    Returns the completed document for download
    """
    try:
        file_stream, filename = await document_generator_service.get_document_stream(
            request.document_id
        )

        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate document: {str(e)}",
        )


@document_router.get("/list")
async def list_documents():
    """List all documents"""
    try:
        documents = await document_service.list_documents()
        return {
            "documents": [
                {
                    "id": str(doc.id),
                    "title": doc.title,
                    "placeholder_count": len(doc.placeholders),
                    "filled_count": sum(
                        1 for p in doc.placeholders if p.value is not None
                    ),
                    "analysis_metadata": doc.analysis_metadata,
                }
                for doc in documents
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}",
        )
