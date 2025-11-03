from bson import ObjectId
from repository.database import db

from models import Document


class DocumentRepository:

    def __init__(self):
        self.collection = db.documents

    async def add_document(self, document: Document) -> str:
        result = await self.collection.insert_one(document.model_dump(by_alias=True))
        return str(result.inserted_id)

    async def get_document_by_id(self, document_id: str) -> Document | None:
        try:
            doc = await self.collection.find_one({"_id": ObjectId(document_id)})
            if doc:
                return Document(**doc)
            return None
        except Exception as e:
            print(f"Error getting document: {e}")
            return None

    async def update_document(self, document_id: str, document: Document) -> bool:
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": document.model_dump(by_alias=True, exclude={"id"})},
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating document: {e}")
            return False


document_repo_ins = DocumentRepository()
