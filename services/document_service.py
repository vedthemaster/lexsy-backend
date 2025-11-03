import os
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from bson import ObjectId
import uuid

from models import Document, PlaceHolder
from repository import  document_repo_ins
from app.openai.parser import OpenAIHandler
from config import config


class DocumentService:

    def __init__(self):
        self.upload_dir = "uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
        self.openai_handler = OpenAIHandler()
        self.assistant_id = config.OPENAI_ASSISTANT_ID  # Add this to your config

    async def validate_file_type(self, file: UploadFile) -> None:
        """Validate that the uploaded file is a .docx file"""
        if not file.filename.endswith(".docx"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only .docx files are allowed.",
            )

    async def save_file(self, file: UploadFile, original_filename: str) -> str:
        """Save the uploaded file to the upload directory with unique ID"""
        unique_id = str(uuid.uuid4())
        # Keep original extension
        file_extension = os.path.splitext(original_filename)[1]
        file_path = os.path.join(self.upload_dir, f"{unique_id}{file_extension}")

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return file_path

    async def extract_placeholders(self, file_path: str) -> list[PlaceHolder]:
        """Extract placeholders from the document using OpenAI"""
        try:
            # Create a new thread
            thread_id = await self.openai_handler.create_thread()

            # Find placeholders
            result = await self.openai_handler.find_placeholders(
                thread_id=thread_id, assistant_id=self.assistant_id, file_path=file_path
            )

            # Convert to PlaceHolder objects
            placeholders = []
            if result and "placeholders" in result:
                for p in result["placeholders"]:
                    placeholders.append(
                        PlaceHolder(
                            name=p.get("name", ""),
                            placeholder=p.get("placeholder", ""),
                            regex=p.get("regex", ""),
                        )
                    )

            return placeholders
        except Exception as e:
            print(f"Error extracting placeholders: {e}")
            return []

    async def upload_and_process_document(self, file: UploadFile) -> Document:
        """
        Main method to handle document upload and processing
        1. Validate file type
        2. Get original filename
        3. Save file to disk with unique ID
        4. Extract placeholders using OpenAI
        5. Create document record with title, placeholders, and path
        6. Save to database
        """
        # Validate file type
        await self.validate_file_type(file)

        # Get original filename
        original_filename = file.filename

        # Save file
        file_path = await self.save_file(file, original_filename)

        # Extract placeholders (using OpenAI handler)
        placeholders = await self.extract_placeholders(file_path)

        # Create document with all required fields
        document = Document(
            title=original_filename, placeholders=placeholders, path=file_path
        )

        # Save to database
        document_id = await document_repo_ins.add_document(document)
        document.id = document_id

        return document

    # async def get_all_documents(self) -> list[Document]:
    #     """Get all documents from the database"""
    #     return await document_repository.get_all()

    # async def get_document_by_id(self, document_id: str) -> Optional[Document]:
    #     """Get a single document by ID"""
    #     return await document_repository.get_by_id(document_id)

    # async def update_document(self, document_id: str, document: Document) -> bool:
    #     """Update a document"""
    #     return await document_repository.update(document_id, document)

    # async def delete_document(self, document_id: str) -> bool:
    #     """Delete a document"""
    #     return await document_repository.delete(document_id)


# Create a singleton instance
document_service = DocumentService()
