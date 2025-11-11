import os
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from bson import ObjectId
import uuid

from ..models import Document, PlaceHolder
from ..repository import document_repo_ins
from ..app.openai import OpenAIParser
from config import config


class DocumentService:

    def __init__(self):
        self.upload_dir = "uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
        self.openai_handler = OpenAIParser()
        self.assistant_id = config.OPENAI_PARSER_ASSISTANT_ID

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
        file_extension = os.path.splitext(original_filename)[1]
        file_path = os.path.join(self.upload_dir, f"{unique_id}{file_extension}")

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return file_path

    async def extract_placeholders(self, file_path: str) -> list[PlaceHolder]:
        """Extract placeholders from the document using OpenAI"""
        try:
            thread_id = await self.openai_handler.create_thread()

            result = await self.openai_handler.find_placeholders(
                thread_id=thread_id, assistant_id=self.assistant_id, file_path=file_path
            )

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
        except ValueError as e:
            error_message = str(e)
            if "no placeholders" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_message,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=error_message,
                )
        except Exception as e:
            print(f"Error extracting placeholders: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing document: {str(e)}. Please try uploading the file again.",
            )

    async def upload_and_process_document(self, file: UploadFile) -> Document:

        await self.validate_file_type(file)

        original_filename = file.filename

        file_path = await self.save_file(file, original_filename)

        placeholders = await self.extract_placeholders(file_path)

        document = Document(
            title=original_filename, placeholders=placeholders, path=file_path
        )

        document_id = await document_repo_ins.add_document(document)
        document.id = document_id

        return document


# Create a singleton instance
document_service = DocumentService()
