from typing import Dict
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from config import config


class ContextAnalysis(BaseModel):
    """Result of context analysis"""

    semantic_meaning: str = Field(description="What this placeholder represents")
    legal_purpose: str = Field(description="Purpose in legal context")
    required_format: str = Field(description="Expected format/structure")
    validation_hints: str = Field(description="How to validate the value")


class ContextAnalyzerTool(BaseTool):
    """Tool to analyze the semantic context around a placeholder"""

    name: str = "context_analyzer"
    description: str = """Analyzes the semantic context around a placeholder to understand its meaning.
    Input should be a JSON string with 'placeholder', 'context_before', and 'context_after'.
    Returns detailed context analysis including semantic meaning and validation hints."""

    llm: ChatOpenAI = Field(
        default_factory=lambda: ChatOpenAI(
            model="gpt-4o-mini", temperature=0, api_key=config.OPENAI_API_KEY
        )
    )

    def _run(self, input_data: str) -> ContextAnalysis:
        """Analyze the context around a placeholder"""
        import json

        data = json.loads(input_data)

        placeholder = data.get("placeholder", "")
        context_before = data.get("context_before", "")
        context_after = data.get("context_after", "")

        prompt = f"""You are analyzing a placeholder in a legal document. Provide detailed context analysis.

Placeholder: {placeholder}
Text before: {context_before}
Text after: {context_after}

Analyze and provide:
1. Semantic meaning: What does this placeholder represent? (e.g., "Party's full legal name", "Contract effective date")
2. Legal purpose: Why is this information needed in the legal document? (e.g., "To identify the contracting party", "To establish contract validity period")
3. Required format: What format should the value be in? (e.g., "Full name in format: First Last", "Date in MM/DD/YYYY format")
4. Validation hints: How can we validate if the provided value is correct? (e.g., "Must be alphabetic characters only", "Must be a valid date")

Respond in JSON format:
{{
    "semantic_meaning": "...",
    "legal_purpose": "...",
    "required_format": "...",
    "validation_hints": "..."
}}"""

        try:
            response = self.llm.predict(prompt)
            # Extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return ContextAnalysis(**result)
            else:
                # Fallback if no JSON found
                return self._fallback_analysis(
                    placeholder, context_before, context_after
                )
        except Exception:
            return self._fallback_analysis(placeholder, context_before, context_after)

    def _fallback_analysis(
        self, placeholder: str, context_before: str, context_after: str
    ) -> ContextAnalysis:
        """Fallback analysis using simple heuristics"""
        placeholder_lower = placeholder.lower()

        # Simple keyword-based analysis
        if "name" in placeholder_lower:
            return ContextAnalysis(
                semantic_meaning="A person's or entity's name",
                legal_purpose="To identify a party in the legal document",
                required_format="Full name, typically First Last or Entity Name",
                validation_hints="Should contain alphabetic characters and possibly spaces",
            )
        elif "date" in placeholder_lower:
            return ContextAnalysis(
                semantic_meaning="A date value",
                legal_purpose="To establish timing or deadline in the document",
                required_format="Date in MM/DD/YYYY or similar format",
                validation_hints="Must be a valid date",
            )
        elif "address" in placeholder_lower:
            return ContextAnalysis(
                semantic_meaning="A physical or mailing address",
                legal_purpose="To identify location for legal purposes",
                required_format="Street, City, State, ZIP",
                validation_hints="Should contain street, city, state components",
            )
        else:
            return ContextAnalysis(
                semantic_meaning="A text value to be filled",
                legal_purpose="Information required for document completion",
                required_format="Text format",
                validation_hints="Should be non-empty text",
            )

    async def _arun(self, input_data: str) -> ContextAnalysis:
        """Async version - not implemented"""
        raise NotImplementedError("Async not supported")
