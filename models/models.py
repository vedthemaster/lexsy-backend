from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict

class MongoModel(BaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")

    model_config = ConfigDict(
        arbitrary_types_allowed=True, json_encoders={ObjectId: str}
    )

class PlaceHolder(BaseModel):
    name: str
    value : Optional[str | int ] = None
    placeholder : str
    regex : str
    
class Document(MongoModel):
    title: str
    placeholders : list[PlaceHolder] = Field(default_factory=list)
    path : str
    
    
