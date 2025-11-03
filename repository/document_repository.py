from repository.database import db

from models import Document

class DocumentRepository:
    
    def __init__(self):
        self.collection = db.documents
        
    async def add_document(self, document: Document) -> str:
        result = await self.collection.insert_one(document.model_dump(by_alias=True))
        return str(result.inserted_id)
    
    
document_repo_ins = DocumentRepository()