"""
Agent-Based Conversational Filler with Validation Pipeline

Architecture: 3-Agent Pipeline
1. Value Extractor Agent → Extracts structured values from conversation
2. Hybrid Validator → Validates with type-specific rules + LLM confidence
3. Response Generator Agent → Creates natural conversational responses

This architecture differs from function-calling approaches by using
a sequential agent pipeline with confidence scoring at each stage.
"""

from typing import Optional, Dict, Any

from api.v2.models.models import PlaceHolder, PlaceholderType
from api.v2.app.langchain.agents import ValueExtractor, ResponseGenerator
from api.v2.app.langchain.validators import HybridValidator


class LangChainFiller:
    """
    Agent-based filler using validation pipeline architecture
    """

    def __init__(self):
        # Initialize the 3-agent pipeline
        self.value_extractor = ValueExtractor()
        self.validator = HybridValidator()
        self.response_generator = ResponseGenerator()

    async def process_message(
        self,
        session_id: str,
        placeholder: PlaceHolder,
        user_message: str,
        conversation_history: list = None,
        progress: dict = None,
    ) -> Dict[str, Any]:
        """Process user message through agent pipeline

        Pipeline Flow:
        1. Extract value from message
        2. If value extracted → Validate
        3. Generate appropriate response based on state
        """

        if conversation_history is None:
            conversation_history = []

        if progress is None:
            progress = {"filled": 0, "total": 1}

        try:
            extraction_result = await self.value_extractor.extract(
                user_message, placeholder, conversation_history
            )

            if (
                extraction_result.extracted_value is None
                or extraction_result.needs_clarification
            ):
                response = await self.response_generator.generate_response(
                    state="NEEDS_CLARIFICATION",
                    current_placeholder=placeholder,
                    next_placeholder=None,
                    extraction_result=extraction_result,
                )

                return {
                    "response": response,
                    "extracted_value": None,
                    "validation_result": None,
                    "value_accepted": False,
                    "needs_clarification": True,
                    "confidence": extraction_result.confidence,
                }

            validation_result = await self.validator.validate(
                value=extraction_result.extracted_value,
                placeholder_type=(
                    placeholder.analysis.inferred_type
                    if placeholder.analysis
                    else PlaceholderType.TEXT
                ),
                context=f"{placeholder.analysis.context_before if placeholder.analysis else ''} ... {placeholder.analysis.context_after if placeholder.analysis else ''}",
                validation_rules=(
                    placeholder.analysis.validation_rules
                    if placeholder.analysis
                    else []
                ),
            )

            if not validation_result.is_valid:
                response = await self.response_generator.generate_response(
                    state="INVALID",
                    current_placeholder=placeholder,
                    next_placeholder=None,
                    validation_result=validation_result,
                )

                return {
                    "response": response,
                    "extracted_value": extraction_result.extracted_value,
                    "validation_result": validation_result.model_dump(),
                    "value_accepted": False,
                    "needs_clarification": False,
                    "confidence": validation_result.confidence,
                }

            overall_confidence = (
                extraction_result.confidence * validation_result.confidence
            )

            return {
                "response": validation_result.validation_message,
                "extracted_value": extraction_result.extracted_value,
                "validation_result": validation_result.model_dump(),
                "value_accepted": True,
                "needs_clarification": False,
                "confidence": overall_confidence,
                "extraction_reasoning": extraction_result.reasoning,
            }

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            print(f"Error in filler pipeline: {error_details}")

            return {
                "response": f"I encountered an error processing your message. Could you try rephrasing? Error: {str(e)}",
                "error": str(e),
                "extracted_value": None,
                "validation_result": None,
                "value_accepted": False,
                "needs_clarification": True,
                "confidence": 0.0,
            }

    async def generate_initial_question(self, placeholder: PlaceHolder) -> str:
        """Generate initial question for a placeholder"""
        return await self.response_generator.generate_initial_question(placeholder)

    async def generate_next_question(
        self,
        next_placeholder: PlaceHolder,
        current_placeholder: PlaceHolder,
        accepted_value: str,
        progress: dict,
    ) -> str:
        """Generate response that confirms current and asks for next"""

        from api.v2.app.langchain.agents.value_extractor import ExtractionResult

        extraction_result = ExtractionResult(
            extracted_value=accepted_value,
            confidence=0.95,
            needs_clarification=False,
            reasoning="Value accepted",
        )

        response = await self.response_generator.generate_response(
            state="ACCEPTED",
            current_placeholder=current_placeholder,
            next_placeholder=next_placeholder,
            extraction_result=extraction_result,
            progress=progress,
        )

        return response

    async def generate_completion_message(self, progress: dict) -> str:
        """Generate completion message"""
        return await self.response_generator.generate_response(
            state="COMPLETED",
            current_placeholder=None,
            next_placeholder=None,
            progress=progress,
        )
