from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# TODO: Import v2 services once implemented
# from services.placeholder_service_v2 import placeholder_service_v2

placeholder_router = APIRouter()


class StartSessionRequest(BaseModel):
    document_id: str


class ContinueConversationRequest(BaseModel):
    document_id: str
    thread_id: str
    message: str


@placeholder_router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_filling_session(request: StartSessionRequest):
    """
    Start a new conversation session using LangChain tools
    TODO: Implement v2 logic
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="V2 start session endpoint not yet implemented",
    )


@placeholder_router.post("/continue")
async def continue_conversation(request: ContinueConversationRequest):
    """
    Continue conversation using LangChain tools
    TODO: Implement v2 logic
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="V2 continue conversation endpoint not yet implemented",
    )
