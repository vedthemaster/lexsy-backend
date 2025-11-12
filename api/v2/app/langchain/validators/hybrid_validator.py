"""
Hybrid Validator: Combines rule-based validation with LLM confidence scoring
"""

from typing import Dict, Any, Optional
import re
from datetime import datetime
from dateutil import parser as date_parser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from api.v2.models.models import PlaceholderType
from config import config


class ValidationResult(BaseModel):
    """Result of hybrid validation"""

    is_valid: bool
    confidence: float  # 0.0 to 1.0
    validation_message: str
    suggested_correction: Optional[str] = None


class HybridValidator:
    """
    Hybrid validator combining:
    1. Rule-based validation (fast, deterministic)
    2. LLM confidence scoring (smart, contextual)
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0, api_key=config.OPENAI_API_KEY
        )

    async def validate(
        self,
        value: str,
        placeholder_type: PlaceholderType,
        context: str = "",
        validation_rules: list = None,
    ) -> ValidationResult:
        """Validate a value using hybrid approach (rules + LLM confidence)"""

        rule_result = self._rule_based_validation(value, placeholder_type)

        if not rule_result["passed"]:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                validation_message=rule_result["message"],
                suggested_correction=rule_result.get("suggestion"),
            )

        llm_confidence = await self._llm_confidence_check(
            value, placeholder_type, context, validation_rules
        )

        if rule_result["confidence"] >= 0.75:
            final_confidence = rule_result["confidence"] * 0.5 + llm_confidence * 0.5
        else:
            final_confidence = rule_result["confidence"] * 0.4 + llm_confidence * 0.6

        return ValidationResult(
            is_valid=final_confidence > 0.5,
            confidence=final_confidence,
            validation_message=self._generate_message(
                final_confidence, placeholder_type
            ),
            suggested_correction=None,
        )

    def _rule_based_validation(
        self, value: str, placeholder_type: PlaceholderType
    ) -> Dict[str, Any]:
        """Fast rule-based validation"""

        if placeholder_type == PlaceholderType.EMAIL:
            return self._validate_email(value)

        elif placeholder_type == PlaceholderType.PHONE:
            return self._validate_phone(value)

        elif placeholder_type == PlaceholderType.DATE:
            return self._validate_date(value)

        elif placeholder_type == PlaceholderType.NUMBER:
            return self._validate_number(value)

        elif placeholder_type == PlaceholderType.ADDRESS:
            return self._validate_address(value)

        else:  # TEXT, UNKNOWN
            return self._validate_text(value)

    def _validate_email(self, value: str) -> Dict[str, Any]:
        """Validate email format"""
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(email_pattern, value):
            return {
                "passed": False,
                "confidence": 0.0,
                "message": "Invalid email format. Please use format like: user@example.com",
                "suggestion": "e.g., john@company.com",
            }

        return {"passed": True, "confidence": 0.95, "message": "Valid email format"}

    def _validate_phone(self, value: str) -> Dict[str, Any]:
        """Validate phone number"""

        digits_only = re.sub(r"[\s\-\(\)\+]", "", value)

        if not digits_only.isdigit():
            return {
                "passed": False,
                "confidence": 0.0,
                "message": "Phone number should contain only digits and separators",
                "suggestion": "e.g., +1-555-123-4567 or 5551234567",
            }

        if len(digits_only) < 10 or len(digits_only) > 15:
            return {
                "passed": False,
                "confidence": 0.0,
                "message": f"Phone number should be 10-15 digits (got {len(digits_only)})",
                "suggestion": "Include country code if international",
            }

        return {"passed": True, "confidence": 0.9, "message": "Valid phone format"}

    def _validate_date(self, value: str) -> Dict[str, Any]:
        """Validate date format"""
        try:
            parsed_date = date_parser.parse(value, fuzzy=False)

            current_year = datetime.now().year
            if parsed_date.year < 1900 or parsed_date.year > current_year + 50:
                return {
                    "passed": False,
                    "confidence": 0.0,
                    "message": f"Date year {parsed_date.year} seems unusual",
                    "suggestion": "Please double-check the year",
                }

            return {"passed": True, "confidence": 0.9, "message": "Valid date format"}

        except (ValueError, OverflowError):
            return {
                "passed": False,
                "confidence": 0.0,
                "message": "Could not parse date. Please use format like: MM/DD/YYYY or YYYY-MM-DD",
                "suggestion": "e.g., 12/25/2024 or 2024-12-25",
            }

    def _validate_number(self, value: str) -> Dict[str, Any]:
        """Validate numeric value"""

        cleaned = re.sub(r"[$,€£¥\s]", "", value)

        try:
            float(cleaned)
            return {"passed": True, "confidence": 0.95, "message": "Valid number"}
        except ValueError:
            return {
                "passed": False,
                "confidence": 0.0,
                "message": "Not a valid number",
                "suggestion": "e.g., 1234.56 or $1,234.56",
            }

    def _validate_address(self, value: str) -> Dict[str, Any]:
        """Validate address (basic checks)"""
        value_stripped = value.strip()

        if len(value_stripped) == 2 and value_stripped.isalpha():
            return {"passed": True, "confidence": 0.85, "message": "Valid (state code)"}

        if len(value_stripped) < 3:
            return {
                "passed": False,
                "confidence": 0.0,
                "message": "Too short",
                "suggestion": "AZ or 123 Main St, City, State",
            }

        has_letters = bool(re.search(r"[a-zA-Z]", value))

        if not has_letters:
            return {
                "passed": False,
                "confidence": 0.0,
                "message": "Invalid format",
                "suggestion": "AZ or 123 Main St, City, State",
            }

        return {"passed": True, "confidence": 0.85, "message": "Valid"}

    def _validate_text(self, value: str) -> Dict[str, Any]:
        """Validate text (basic checks)"""
        value_stripped = value.strip()

        if len(value_stripped) == 0:
            return {
                "passed": False,
                "confidence": 0.0,
                "message": "Value cannot be empty",
                "suggestion": None,
            }

        if len(value_stripped) == 1:
            return {
                "passed": True,
                "confidence": 0.75,
                "message": "Valid (short input)",
            }

        return {"passed": True, "confidence": 0.9, "message": "Valid"}

    async def _llm_confidence_check(
        self,
        value: str,
        placeholder_type: PlaceholderType,
        context: str,
        validation_rules: list,
    ) -> float:
        """Use LLM to score confidence in context"""

        prompt = f"""Validate this input for a legal document.

Type: {placeholder_type.value}
Value: "{value}"
Context: {context[:200]}

Rate confidence 0.0-1.0:
- 0.9-1.0: Perfect match
- 0.7-0.89: Good, acceptable
- 0.5-0.69: Questionable but might work
- 0.0-0.49: Invalid

Be lenient for TEXT type. Names, companies, addresses with reasonable format should score 0.8+.

Respond with ONLY a number (e.g., 0.85):"""

        try:
            response = self.llm.invoke(prompt).content.strip()
            confidence = float(response)
            return max(0.0, min(1.0, confidence))
        except Exception as e:
            print(f"LLM confidence check failed: {e}")
            return 0.7

    def _generate_message(
        self, confidence: float, placeholder_type: PlaceholderType
    ) -> str:
        """Generate appropriate validation message"""

        if confidence >= 0.6:
            return "Accepted"
        else:
            return f"Invalid {placeholder_type.value}"
