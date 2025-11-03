from pydantic import BaseModel

class FillRequest(BaseModel):
    document_id : str
    