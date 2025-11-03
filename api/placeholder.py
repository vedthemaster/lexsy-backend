from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from services.placeholder_service import placeholder_service

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
    Start a new conversation session for filling placeholders
    Returns thread_id and initial conversation history
    """
    try:
        result = await placeholder_service.start_filling_session(request.document_id)
        return {
            "success": True,
            "thread_id": result["thread_id"],
            "conversation": result["conversation"],
            "all_filled": result["all_filled"],
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting session: {str(e)}",
        )


@placeholder_router.post("/continue")
async def continue_conversation(request: ContinueConversationRequest):
    """
    Continue the conversation with user's response
    Returns updated conversation history and completion status
    """
    try:
        result = await placeholder_service.continue_conversation(
            request.document_id, request.thread_id, request.message
        )
        return {
            "success": True,
            "conversation": result["conversation"],
            "all_filled": result["all_filled"],
            "message": (
                "All placeholders filled! Ready to generate document."
                if result["all_filled"]
                else "Continue filling placeholders"
            ),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}",
        )
