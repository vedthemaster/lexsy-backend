from typing import List
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import re
from datetime import datetime

from config import config


class ValidationResult(BaseModel):
    """Result of value validation"""

    is_valid: bool = Field(description="Whether the value is valid")
    confidence: float = Field(description="Confidence in validation (0-1)")
    errors: List[str] = Field(
        default_factory=list, description="Validation errors if any"
    )
    suggestions: List[str] = Field(
        default_factory=list, description="Suggestions for correction"
    )


class ValidationTool(BaseTool):
    """Tool to validate placeholder values against expected formats and constraints"""

    name: str = "value_validator"
    description: str = """Validates a value for a placeholder against expected format and constraints.
    Input should be a JSON string with 'value', 'placeholder_type', 'validation_rules', and 'context'.
    Returns validation result with errors and suggestions."""

    llm: ChatOpenAI = Field(
        default_factory=lambda: ChatOpenAI(
            model="gpt-4o-mini", temperature=0, api_key=config.OPENAI_API_KEY
        )
    )

    def _run(self, input_data: str) -> ValidationResult:
        """Validate a placeholder value"""
        import json

        data = json.loads(input_data)

        value = data.get("value", "")
        placeholder_type = data.get("placeholder_type", "TEXT")
        validation_rules = data.get("validation_rules", "")
        context = data.get("context", "")

        # First, apply rule-based validation
        rule_result = self._rule_based_validation(value, placeholder_type)

        if not rule_result.is_valid:
            return rule_result

        # If rules pass, use LLM for semantic validation
        return self._llm_validation(value, placeholder_type, validation_rules, context)

    def _rule_based_validation(
        self, value: str, placeholder_type: str
    ) -> ValidationResult:
        """Apply rule-based validation patterns"""
        value = value.strip()

        if not value:
            return ValidationResult(
                is_valid=False,
                confidence=1.0,
                errors=["Value cannot be empty"],
                suggestions=["Please provide a value"],
            )

        if placeholder_type == "EMAIL":
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, value):
                return ValidationResult(
                    is_valid=False,
                    confidence=0.95,
                    errors=["Invalid email format"],
                    suggestions=["Email should be in format: user@example.com"],
                )

        elif placeholder_type == "PHONE":
            # Remove common formatting characters
            phone_digits = re.sub(r"[^\d]", "", value)
            if len(phone_digits) < 10:
                return ValidationResult(
                    is_valid=False,
                    confidence=0.9,
                    errors=["Phone number too short"],
                    suggestions=["Phone should have at least 10 digits"],
                )

        elif placeholder_type == "DATE":
            # Try common date formats
            date_formats = ["%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%B %d, %Y"]
            date_valid = False
            for fmt in date_formats:
                try:
                    datetime.strptime(value, fmt)
                    date_valid = True
                    break
                except ValueError:
                    continue

            if not date_valid:
                return ValidationResult(
                    is_valid=False,
                    confidence=0.9,
                    errors=["Invalid date format"],
                    suggestions=["Use format MM/DD/YYYY or YYYY-MM-DD"],
                )

        elif placeholder_type == "NUMBER":
            try:
                float(value.replace(",", ""))
            except ValueError:
                return ValidationResult(
                    is_valid=False,
                    confidence=0.95,
                    errors=["Value is not a valid number"],
                    suggestions=["Provide a numeric value"],
                )

        elif placeholder_type == "BOOLEAN":
            valid_booleans = ["yes", "no", "true", "false", "y", "n", "1", "0"]
            if value.lower() not in valid_booleans:
                return ValidationResult(
                    is_valid=False,
                    confidence=0.9,
                    errors=["Value should be Yes/No or True/False"],
                    suggestions=["Use: Yes, No, True, or False"],
                )

        # If all rule-based checks pass
        return ValidationResult(
            is_valid=True, confidence=0.8, errors=[], suggestions=[]
        )

    def _llm_validation(
        self, value: str, placeholder_type: str, validation_rules: str, context: str
    ) -> ValidationResult:
        """Use LLM for semantic validation"""
        prompt = f"""You are validating a value for a placeholder in a legal document.

Value provided: {value}
Expected type: {placeholder_type}
Validation rules: {validation_rules}
Context: {context}

Assess if this value makes sense semantically:
- Does it match the expected type?
- Is it appropriate for the legal context?
- Are there any concerns about the value?

Respond in JSON format:
{{
    "is_valid": true/false,
    "confidence": 0.0-1.0,
    "errors": ["list of errors if invalid"],
    "suggestions": ["list of suggestions if needed"]
}}"""

        try:
            response = self.llm.predict(prompt)
            # Extract JSON from response
            import re

            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                import json

                result = json.loads(json_match.group())
                return ValidationResult(**result)
            else:
                # If can't parse, assume valid
                return ValidationResult(
                    is_valid=True, confidence=0.7, errors=[], suggestions=[]
                )
        except Exception:
            # On error, assume valid (permissive)
            return ValidationResult(
                is_valid=True, confidence=0.6, errors=[], suggestions=[]
            )

    async def _arun(self, input_data: str) -> ValidationResult:
        """Async version - not implemented"""
        raise NotImplementedError("Async not supported")
