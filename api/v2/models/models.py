from typing import Optional, List
from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict


class MongoModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")

    model_config = ConfigDict(populate_by_name=True)


class PlaceholderType(str, Enum):
    """Inferred data types for placeholders"""

    TEXT = "text"
    DATE = "date"
    NUMBER = "number"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


class PlaceholderAnalysis(BaseModel):
    """Enhanced analysis for each placeholder using LangChain tools"""

    context_before: str = Field(
        default="", description="Text appearing before placeholder"
    )
    context_after: str = Field(
        default="", description="Text appearing after placeholder"
    )
    inferred_type: PlaceholderType = Field(default=PlaceholderType.UNKNOWN)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    validation_rules: List[str] = Field(default_factory=list)
    suggested_value: Optional[str] = None
    related_placeholders: List[str] = Field(default_factory=list)
    question_hint: Optional[str] = None


class PlaceHolder(BaseModel):
    """Extended placeholder model with LangChain analysis"""

    name: str
    value: Optional[str | int] = None
    placeholder: str  # Original placeholder text like "[Company Name]"
    unique_marker: str  # Unique marker like "{{PLACEHOLDER_UUID_123}}"
    regex: str
    analysis: Optional[PlaceholderAnalysis] = None  # Enhanced with LangChain


class ConversationMessage(BaseModel):
    """Single message in conversation history"""

    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    confidence: Optional[float] = None  # For assistant messages


class Document(MongoModel):
    """Document model - compatible with V1 structure"""

    title: str
    placeholders: List[PlaceHolder] = Field(default_factory=list)
    path: str  # Original uploaded document path
    temp_path: Optional[str] = None  # Template document with unique markers
    # V2 specific fields - Agent Pipeline
    langchain_session_id: Optional[str] = None  # For tracking LangChain conversation
    conversation_history: List[ConversationMessage] = Field(
        default_factory=list
    )  # Persistent conversation
    analysis_metadata: Optional[dict] = None  # Store agent decisions
