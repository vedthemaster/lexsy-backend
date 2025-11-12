"""
Value Extractor Agent: Extracts structured values from conversational input
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from api.v2.models.models import PlaceHolder, PlaceholderType
from config import config


class ExtractionResult(BaseModel):
    """Result of value extraction"""

    extracted_value: Optional[str]
    confidence: float  # 0.0 to 1.0
    needs_clarification: bool
    reasoning: str


class ValueExtractor:
    """
    Agent specialized in extracting structured values from user messages
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,  # Low temperature for consistent extraction
            api_key=config.OPENAI_API_KEY,
        )

    async def extract(
        self,
        user_message: str,
        placeholder: PlaceHolder,
        conversation_history: list = None,
    ) -> ExtractionResult:
        """Extract value from user message"""

        context_parts = []

        if placeholder.analysis:
            context_parts.append(
                f"Expected Type: {placeholder.analysis.inferred_type.value}"
            )
            context_parts.append(
                f"Context: {placeholder.analysis.context_before}...{placeholder.analysis.context_after}"
            )

            if placeholder.analysis.validation_rules:
                context_parts.append(
                    f"Rules: {', '.join(placeholder.analysis.validation_rules)}"
                )

        context_str = "\n".join(context_parts)

        history_str = ""
        if conversation_history:
            recent_history = conversation_history[-4:]
            history_str = "\n".join(
                [f"{msg['role']}: {msg['content']}" for msg in recent_history]
            )

        prompt = f"""Extract the value from user's message.

Placeholder: {placeholder.name}
Type: {placeholder.analysis.inferred_type.value if placeholder.analysis else 'text'}
User said: "{user_message}"

TASK: Extract ONLY the actual value, removing filler words.

EXAMPLES:
"My company name is Lexsy" → "Lexsy"
"It's Acme Corporation" → "Acme Corporation"
"The investor name is YC and it is company" → "YC"
"John Smith" → "John Smith"
"john@example.com" → "john@example.com"
"The date is 12/25/2024" → "12/25/2024"
"123 Main Street, Tempe, Arizona" → "123 Main Street, Tempe, Arizona"
"What format?" → null (question, needs clarification)
"I'm not sure" → null (unclear)
"yes" → null (ambiguous)

BE AGGRESSIVE: Extract the value even from long sentences. Look for the actual content after "is", "name is", "it's", etc.

JSON response:
{{
    "extracted_value": "extracted value or null",
    "confidence": 0.9,
    "needs_clarification": false,
    "reasoning": "Extracted from sentence"
}}"""

        try:
            response = self.llm.invoke(prompt).content.strip()

            import json

            if "{" in response:
                json_start = response.index("{")
                json_end = response.rindex("}") + 1
                json_str = response[json_start:json_end]
                result_dict = json.loads(json_str)
            else:
                result_dict = json.loads(response)

            return ExtractionResult(**result_dict)

        except Exception as e:
            print(f"Value extraction failed: {e}")
            return self._fallback_extraction(user_message, placeholder)

    def _fallback_extraction(
        self, message: str, placeholder: PlaceHolder
    ) -> ExtractionResult:
        """Fallback extraction when LLM fails - use pattern matching"""

        import re

        message = message.strip()

        question_words = ["what", "how", "why", "when", "where", "which", "who", "?"]
        is_question = any(word in message.lower() for word in question_words)

        if is_question:
            return ExtractionResult(
                extracted_value=None,
                confidence=0.0,
                needs_clarification=True,
                reasoning="Message appears to be a question",
            )

        if len(message) < 2:
            return ExtractionResult(
                extracted_value=None,
                confidence=0.0,
                needs_clarification=True,
                reasoning="Message too short",
            )

        patterns = [
            r"(?:is|are|was|were)\s+(.+)$",
            r"(?:it's|its)\s+(.+)$",
            r"(?:called|named)\s+(.+)$",
            r"^(.+?)\s+(?:is|was|are).*",
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                extracted = re.sub(
                    r"\s+and\s+it.*$", "", extracted, flags=re.IGNORECASE
                )
                if extracted and len(extracted) > 1:
                    return ExtractionResult(
                        extracted_value=extracted,
                        confidence=0.75,
                        needs_clarification=False,
                        reasoning="Extracted using pattern matching",
                    )

        if len(message) < 200:
            return ExtractionResult(
                extracted_value=message,
                confidence=0.6,
                needs_clarification=False,
                reasoning="Direct input without pattern",
            )

        return ExtractionResult(
            extracted_value=None,
            confidence=0.0,
            needs_clarification=True,
            reasoning="Message too complex",
        )
