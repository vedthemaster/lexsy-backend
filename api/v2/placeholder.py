from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from api.v2.services import placeholder_service

placeholder_router = APIRouter()


class StartSessionRequest(BaseModel):
    document_id: str


class ContinueConversationRequest(BaseModel):
    session_id: str
    message: str


class SessionStatusRequest(BaseModel):
    session_id: str


@placeholder_router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_filling_session(request: StartSessionRequest):
    """
    Start a new conversation session using LangChain tools
    - Creates conversation memory
    - Returns first placeholder with intelligent question
    """
    try:
        result = await placeholder_service.start_session(request.document_id)
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start session: {str(e)}",
        )


@placeholder_router.post("/continue")
async def continue_conversation(request: ContinueConversationRequest):
    """
    Continue conversation using LangChain tools
    - Uses conversation memory for context
    - Validates responses with custom validation tool
    - Provides adaptive questions
    """
    try:
        result = await placeholder_service.process_message(
            request.session_id, request.message
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}",
        )


@placeholder_router.post("/status")
async def get_session_status(request: SessionStatusRequest):
    """
    Get the current status of a conversation session
    Returns progress and current placeholder
    """
    try:
        result = await placeholder_service.get_session_status(request.session_id)
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session status: {str(e)}",
        )
