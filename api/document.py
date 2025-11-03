from fastapi import APIRouter, HTTPException, Depends, HTTPException, status, UploadFile, Request, File
from pydantic import BaseModel

from models import Document
from services.document_service import document_service

document_router = APIRouter()

# @document_router.get("/", status_code=200)
# async def get_documents():
#     return 

@document_router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)):
    document = await document_service.upload_and_process_document(file)
    return {
        "message": "Document uploaded successfully",
        "document": document.title
    }   
        
    
    