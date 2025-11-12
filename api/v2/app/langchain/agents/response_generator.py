"""
Response Generator Agent: Creates natural conversational responses
"""

from typing import Optional
from langchain_openai import ChatOpenAI

from api.v2.models.models import PlaceHolder
from api.v2.app.langchain.validators.hybrid_validator import ValidationResult
from api.v2.app.langchain.agents.value_extractor import ExtractionResult
from config import config


class ResponseGenerator:
    """
    Agent specialized in generating natural conversational responses
    Based on validation state and context
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,  # Higher temperature for natural conversation
            api_key=config.OPENAI_API_KEY,
        )

    async def generate_response(
        self,
        state: str,  # "ACCEPTED", "NEEDS_CLARIFICATION", "INVALID", "COMPLETED"
        current_placeholder: Optional[PlaceHolder],
        next_placeholder: Optional[PlaceHolder],
        extraction_result: Optional[ExtractionResult] = None,
        validation_result: Optional[ValidationResult] = None,
        progress: dict = None,
    ) -> str:
        """
        Generate appropriate response based on state
        """

        if state == "ACCEPTED":
            return await self._generate_accepted_response(
                current_placeholder, next_placeholder, extraction_result, progress
            )

        elif state == "NEEDS_CLARIFICATION":
            return await self._generate_clarification_request(
                current_placeholder, extraction_result
            )

        elif state == "INVALID":
            return await self._generate_invalid_response(
                current_placeholder, validation_result
            )

        elif state == "COMPLETED":
            return await self._generate_completion_message(progress)

        else:
            return "I'm ready to help. What would you like to provide?"

    async def _generate_accepted_response(
        self,
        current_placeholder: PlaceHolder,
        next_placeholder: Optional[PlaceHolder],
        extraction_result: ExtractionResult,
        progress: dict,
    ) -> str:
        """Generate response when value accepted"""

        if not next_placeholder:
            return f"✓ Perfect! I've recorded '{extraction_result.extracted_value}' for {current_placeholder.name}.\n\n🎉 That's everything! All placeholders are filled. You can now generate your completed document."

        confirmation = f"✓ Got it: {extraction_result.extracted_value}"

        next_question = await self.generate_initial_question(next_placeholder)

        progress_text = f"({progress['filled']}/{progress['total']} completed)"

        return f"{confirmation}\n\n{next_question} {progress_text}"

    async def _generate_clarification_request(
        self, placeholder: PlaceHolder, extraction_result: ExtractionResult
    ) -> str:
        """Generate clarification request"""

        question = await self.generate_initial_question(placeholder)
        return f"I need more information. {question}"

    async def _generate_invalid_response(
        self, placeholder: PlaceHolder, validation_result: ValidationResult
    ) -> str:
        """Generate response for invalid input"""

        message = validation_result.validation_message
        if validation_result.suggested_correction:
            message += f"\n\nExample: {validation_result.suggested_correction}"

        message += f"\n\nPlease provide a valid {placeholder.name}."
        return message

    async def _generate_completion_message(self, progress: dict) -> str:
        """Generate completion message"""

        return f"""🎉 Congratulations! All {progress['total']} placeholders have been successfully filled!

Your document is ready to be generated. You can now download your completed document with all the information you've provided.

Would you like to generate the final document now?"""

    async def generate_initial_question(self, placeholder: PlaceHolder) -> str:
        """Generate initial question for a placeholder"""

        if placeholder.analysis and placeholder.analysis.question_hint:
            return placeholder.analysis.question_hint

        if placeholder.name and placeholder.name.strip():
            return f"What is the {placeholder.name}?"

        return "Could you please provide the required information?"
