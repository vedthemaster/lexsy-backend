from typing import Dict, Any
import uuid
from datetime import datetime

from api.v2.models.models import PlaceHolder, ConversationMessage
from api.v2.repository.document_repository import document_repo_ins
from api.v2.app.langchain.filler import LangChainFiller


class PlaceholderService:
    """Service for managing conversational placeholder filling with Agent Pipeline"""

    def __init__(self):
        self.filler = LangChainFiller()
        self.active_sessions: Dict[str, str] = {}  # session_id -> document_id

    async def start_session(self, document_id: str) -> Dict[str, Any]:
        """Start a new conversation session for filling placeholders"""

        # Get document
        document = await document_repo_ins.find_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Create session ID
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = document_id

        # Save session to document
        await document_repo_ins.update_langchain_session(document_id, session_id)

        # Get first unfilled placeholder
        first_placeholder = next(
            (p for p in document.placeholders if p.value is None), None
        )

        if not first_placeholder:
            return {
                "success": True,
                "session_id": session_id,
                "conversation": [],
                "all_filled": True,
                "message": "All placeholders are already filled!",
                "current_placeholder": None,
                "completed": True,
            }

        # Generate initial question using Response Generator
        initial_message = await self.filler.generate_initial_question(first_placeholder)

        conversation_msg = ConversationMessage(
            role="assistant",
            content=initial_message,
            timestamp=datetime.now().isoformat(),
        )
        document.conversation_history.append(conversation_msg)
        await document_repo_ins.save(document)

        return {
            "success": True,
            "session_id": session_id,
            "conversation": [
                {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
                for msg in document.conversation_history
            ],
            "all_filled": False,
            "message": initial_message,
            "current_placeholder": first_placeholder.model_dump(),
            "completed": False,
            "progress": self._calculate_progress(document),
        }

    async def process_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Process a user message through the agent pipeline"""

        # Get document
        document_id = self.active_sessions.get(session_id)
        if not document_id:
            raise ValueError("Invalid session ID")

        document = await document_repo_ins.find_by_id(document_id)
        if not document:
            raise ValueError("Document not found")

        # Get current placeholder (first unfilled)
        current_placeholder = next(
            (p for p in document.placeholders if p.value is None), None
        )

        if not current_placeholder:
            completion_msg = "All placeholders have been filled! You can now download your completed document."

            # Save to conversation history
            document.conversation_history.append(
                ConversationMessage(
                    role="assistant",
                    content=completion_msg,
                    timestamp=datetime.now().isoformat(),
                )
            )
            await document_repo_ins.save(document)

            return {
                "success": True,
                "conversation": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp,
                    }
                    for msg in document.conversation_history
                ],
                "all_filled": True,
                "message": completion_msg,
                "response": completion_msg,
                "current_placeholder": None,
                "next_placeholder": None,
                "completed": True,
                "value_accepted": False,
                "progress": self._calculate_progress(document),
            }

        # Save user message to conversation history
        user_msg = ConversationMessage(
            role="user", content=message, timestamp=datetime.now().isoformat()
        )
        document.conversation_history.append(user_msg)

        # Convert conversation history to format expected by agents
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in document.conversation_history
        ]

        # Calculate progress
        progress = self._calculate_progress(document)

        # Process message through agent pipeline
        result = await self.filler.process_message(
            session_id=session_id,
            placeholder=current_placeholder,
            user_message=message,
            conversation_history=conversation_history,
            progress=progress,
        )

        # If value was accepted, update placeholder and move to next
        if result.get("value_accepted"):
            current_placeholder.value = result["extracted_value"]

            # Get next placeholder
            next_placeholder = next(
                (p for p in document.placeholders if p.value is None), None
            )

            # Update progress
            progress = self._calculate_progress(document)

            if next_placeholder:
                # Generate smooth transition with Response Generator
                response = await self.filler.generate_next_question(
                    next_placeholder=next_placeholder,
                    current_placeholder=current_placeholder,
                    accepted_value=result["extracted_value"],
                    progress=progress,
                )

                # Save assistant response with confidence
                assistant_msg = ConversationMessage(
                    role="assistant",
                    content=response,
                    timestamp=datetime.now().isoformat(),
                    confidence=result.get("confidence"),
                )
                document.conversation_history.append(assistant_msg)

                # Update document in database
                await document_repo_ins.save(document)

                return {
                    "success": True,
                    "conversation": [
                        {
                            "role": msg.role,
                            "content": msg.content,
                            "timestamp": msg.timestamp,
                        }
                        for msg in document.conversation_history
                    ],
                    "all_filled": False,
                    "message": response,
                    "response": response,
                    "current_placeholder": next_placeholder.model_dump(),
                    "next_placeholder": next_placeholder.model_dump(),
                    "completed": False,
                    "value_accepted": True,
                    "confidence": result.get("confidence"),
                    "progress": progress,
                }
            else:
                # All placeholders filled - generate completion message
                completion_msg = await self.filler.generate_completion_message(progress)

                # Save completion message
                assistant_msg = ConversationMessage(
                    role="assistant",
                    content=completion_msg,
                    timestamp=datetime.now().isoformat(),
                    confidence=result.get("confidence"),
                )
                document.conversation_history.append(assistant_msg)

                # Save final document
                await document_repo_ins.save(document)

                return {
                    "success": True,
                    "conversation": [
                        {
                            "role": msg.role,
                            "content": msg.content,
                            "timestamp": msg.timestamp,
                        }
                        for msg in document.conversation_history
                    ],
                    "all_filled": True,
                    "message": completion_msg,
                    "response": completion_msg,
                    "current_placeholder": None,
                    "next_placeholder": None,
                    "completed": True,
                    "value_accepted": True,
                    "confidence": result.get("confidence"),
                    "progress": progress,
                }

        # Value not accepted or needs clarification
        # Save assistant response
        assistant_msg = ConversationMessage(
            role="assistant",
            content=result["response"],
            timestamp=datetime.now().isoformat(),
            confidence=result.get("confidence"),
        )
        document.conversation_history.append(assistant_msg)
        await document_repo_ins.save(document)

        return {
            "success": True,
            "conversation": [
                {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
                for msg in document.conversation_history
            ],
            "all_filled": False,
            "message": result["response"],
            "response": result["response"],
            "current_placeholder": current_placeholder.model_dump(),
            "next_placeholder": None,
            "completed": False,
            "value_accepted": False,
            "validation_result": result.get("validation_result"),
            "needs_clarification": result.get("needs_clarification"),
            "confidence": result.get("confidence"),
            "progress": progress,
        }

    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the status of a conversation session"""

        document_id = self.active_sessions.get(session_id)
        if not document_id:
            raise ValueError("Invalid session ID")

        document = await document_repo_ins.find_by_id(document_id)
        if not document:
            raise ValueError("Document not found")

        progress = self._calculate_progress(document)

        current_placeholder = next(
            (p for p in document.placeholders if p.value is None), None
        )

        return {
            "session_id": session_id,
            "document_id": document_id,
            "filled_count": progress["filled"],
            "total_count": progress["total"],
            "completed": progress["filled"] == progress["total"],
            "current_placeholder": (
                current_placeholder.model_dump() if current_placeholder else None
            ),
            "conversation_history": [
                msg.model_dump() for msg in document.conversation_history
            ],
        }

    def _calculate_progress(self, document) -> dict:
        """Calculate filling progress"""
        filled_count = sum(1 for p in document.placeholders if p.value is not None)
        total_count = len(document.placeholders)

        return {
            "filled": filled_count,
            "total": total_count,
            "percentage": round(
                (filled_count / total_count * 100) if total_count > 0 else 0, 1
            ),
        }


# Singleton instance
placeholder_service = PlaceholderService()
