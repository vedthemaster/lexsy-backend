from typing import List
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from api.v2.models.models import PlaceholderType
from config import config


class PlaceholderClassification(BaseModel):
    """Result of placeholder classification"""

    type: PlaceholderType = Field(description="Classified type")
    confidence: float = Field(description="Confidence score (0-1)")
    reasoning: str = Field(description="Why this type was chosen")


class PlaceholderClassifierTool(BaseTool):
    """Tool to classify placeholder types using LLM reasoning"""

    name: str = "placeholder_classifier"
    description: str = """Classifies a placeholder into specific types (TEXT, DATE, NUMBER, EMAIL, etc.).
    Input should be a JSON string with 'placeholder', 'semantic_meaning', and 'context'.
    Returns the classified type with confidence score."""

    llm: ChatOpenAI = Field(
        default_factory=lambda: ChatOpenAI(
            model="gpt-4o-mini", temperature=0, api_key=config.OPENAI_API_KEY
        )
    )

    def _run(self, input_data: str) -> PlaceholderClassification:
        """Classify the placeholder type"""
        import json

        data = json.loads(input_data)

        placeholder = data.get("placeholder", "")
        semantic_meaning = data.get("semantic_meaning", "")
        context = data.get("context", "")

        # List available types
        type_descriptions = {
            "TEXT": "General text content (names, descriptions, general information)",
            "DATE": "Date values (contract dates, deadlines, birthdates)",
            "NUMBER": "Numeric values (amounts, quantities, counts)",
            "EMAIL": "Email addresses",
            "PHONE": "Phone numbers",
            "ADDRESS": "Physical addresses",
            "BOOLEAN": "Yes/No or True/False values",
            "UNKNOWN": "Cannot determine type",
        }

        types_list = "\n".join([f"- {k}: {v}" for k, v in type_descriptions.items()])

        prompt = f"""You are classifying a placeholder in a legal document.

Placeholder: {placeholder}
Semantic meaning: {semantic_meaning}
Context: {context}

Available types:
{types_list}

Classify this placeholder into ONE of the above types. Consider:
- What kind of information is being requested?
- What format would the answer take?
- Are there specific keywords that indicate the type?

Respond in JSON format:
{{
    "type": "ONE_OF_THE_TYPES_ABOVE",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why this type"
}}"""

        try:
            response = self.llm.predict(prompt)
            # Extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                # Validate and convert type
                type_str = result.get("type", "UNKNOWN")
                try:
                    placeholder_type = PlaceholderType[type_str]
                except KeyError:
                    placeholder_type = PlaceholderType.UNKNOWN

                return PlaceholderClassification(
                    type=placeholder_type,
                    confidence=float(result.get("confidence", 0.5)),
                    reasoning=result.get(
                        "reasoning", "Classification based on LLM analysis"
                    ),
                )
            else:
                return self._fallback_classification(placeholder, semantic_meaning)
        except Exception:
            return self._fallback_classification(placeholder, semantic_meaning)

    def _fallback_classification(
        self, placeholder: str, semantic_meaning: str
    ) -> PlaceholderClassification:
        """Fallback classification using keyword matching"""
        text = (placeholder + " " + semantic_meaning).lower()

        # Check for specific types with keywords
        if any(word in text for word in ["email", "e-mail"]):
            return PlaceholderClassification(
                type=PlaceholderType.EMAIL,
                confidence=0.9,
                reasoning="Contains email-related keywords",
            )
        elif any(word in text for word in ["phone", "telephone", "mobile", "cell"]):
            return PlaceholderClassification(
                type=PlaceholderType.PHONE,
                confidence=0.9,
                reasoning="Contains phone-related keywords",
            )
        elif any(
            word in text for word in ["address", "street", "city", "state", "zip"]
        ):
            return PlaceholderClassification(
                type=PlaceholderType.ADDRESS,
                confidence=0.8,
                reasoning="Contains address-related keywords",
            )
        elif any(word in text for word in ["date", "day", "month", "year", "when"]):
            return PlaceholderClassification(
                type=PlaceholderType.DATE,
                confidence=0.8,
                reasoning="Contains date-related keywords",
            )
        elif any(
            word in text
            for word in ["number", "amount", "quantity", "count", "price", "cost"]
        ):
            return PlaceholderClassification(
                type=PlaceholderType.NUMBER,
                confidence=0.7,
                reasoning="Contains number-related keywords",
            )
        elif any(
            word in text for word in ["yes/no", "true/false", "boolean", "confirm"]
        ):
            return PlaceholderClassification(
                type=PlaceholderType.BOOLEAN,
                confidence=0.7,
                reasoning="Contains boolean-related keywords",
            )
        else:
            return PlaceholderClassification(
                type=PlaceholderType.TEXT,
                confidence=0.6,
                reasoning="Default to TEXT type",
            )

    async def _arun(self, input_data: str) -> PlaceholderClassification:
        """Async version - not implemented"""
        raise NotImplementedError("Async not supported")
