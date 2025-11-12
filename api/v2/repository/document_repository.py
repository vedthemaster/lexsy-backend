from typing import List, Optional
from bson import ObjectId

from database.database import db
from api.v2.models.models import Document, PlaceHolder


class DocumentRepository:
    def __init__(self):
        self.collection = db["documents"]

    async def save(self, document: Document) -> Document:
        """Save or update a document"""
        if document.id:
            # Update existing document
            doc_dict = document.model_dump(by_alias=True, exclude={"id"})
            await self.collection.update_one(
                {"_id": ObjectId(document.id)}, {"$set": doc_dict}
            )
            return document
        else:
            # Insert new document
            doc_dict = document.model_dump(by_alias=True, exclude={"id"})
            result = await self.collection.insert_one(doc_dict)
            document.id = str(result.inserted_id)
            return document

    async def find_by_id(self, document_id: str) -> Optional[Document]:
        """Find a document by ID"""
        doc_dict = await self.collection.find_one({"_id": ObjectId(document_id)})
        if doc_dict:
            doc_dict["_id"] = str(doc_dict["_id"])  # Convert ObjectId to str
            return Document(**doc_dict)
        return None

    async def find_all(self) -> List[Document]:
        """Find all documents"""
        cursor = self.collection.find()
        documents = []
        async for doc_dict in cursor:
            doc_dict["_id"] = str(doc_dict["_id"])  # Convert ObjectId to str
            documents.append(Document(**doc_dict))
        return documents

    async def delete_by_id(self, document_id: str) -> bool:
        """Delete a document by ID"""
        result = await self.collection.delete_one({"_id": ObjectId(document_id)})
        return result.deleted_count > 0

    async def update_placeholders(
        self, document_id: str, placeholders: List[PlaceHolder]
    ) -> bool:
        """Update placeholders for a document"""
        placeholder_dicts = [p.model_dump(by_alias=True) for p in placeholders]
        result = await self.collection.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"placeholders": placeholder_dicts}},
        )
        return result.modified_count > 0

    async def update_langchain_session(self, document_id: str, session_id: str) -> bool:
        """Update LangChain session ID for a document"""
        result = await self.collection.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"langchain_session_id": session_id}},
        )
        return result.modified_count > 0

    async def update_analysis_metadata(self, document_id: str, metadata: dict) -> bool:
        """Update analysis metadata for a document"""
        result = await self.collection.update_one(
            {"_id": ObjectId(document_id)}, {"$set": {"analysis_metadata": metadata}}
        )
        return result.modified_count > 0


# Singleton instance
document_repo_ins = DocumentRepository()
