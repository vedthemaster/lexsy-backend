from typing import List, Tuple, ClassVar
import re
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from config import config


class PlaceholderDetection(BaseModel):
    """Result of placeholder detection"""

    text: str = Field(description="The detected placeholder text")
    start_pos: int = Field(description="Starting position in document")
    end_pos: int = Field(description="Ending position in document")
    context_before: str = Field(description="Text before the placeholder")
    context_after: str = Field(description="Text after the placeholder")
    confidence: float = Field(description="Confidence score (0-1)")


class PlaceholderDetectorTool(BaseTool):
    """Tool to detect placeholders in document text using pattern matching + LLM validation"""

    name: str = "placeholder_detector"
    description: str = """Detects placeholders in document text. 
    Input should be the document text as a string.
    Returns list of detected placeholders with their positions and surrounding context."""

    llm: ChatOpenAI = Field(
        default_factory=lambda: ChatOpenAI(
            model="gpt-4o-mini", temperature=0, api_key=config.OPENAI_API_KEY
        )
    )

    # Common placeholder patterns - more restrictive to avoid false positives
    PLACEHOLDER_PATTERNS: ClassVar[List[str]] = [
        r"\[([A-Z][A-Za-z\s]{2,50})\]",  # [Capitalized Placeholder] - common in legal docs
        r"\[([A-Za-z_\s]{3,50})\]",  # [Generic Placeholder]
        r"\{([A-Za-z_\s]{3,50})\}",  # {PLACEHOLDER}
        r"<([A-Za-z_\s]{3,50})>",  # <PLACEHOLDER>
        r"{{([A-Za-z_\s]{3,50})}}",  # {{PLACEHOLDER}}
        r"\[\[([A-Za-z_\s]{3,50})\]\]",  # [[PLACEHOLDER]]
        r"\[_{2,10}\]",  # [__] or [___] - blank lines to fill
    ]

    def _run(self, document_text: str) -> List[PlaceholderDetection]:
        """Detect placeholders in the document"""
        detections = []

        for pattern in self.PLACEHOLDER_PATTERNS:
            for match in re.finditer(pattern, document_text):
                placeholder_text = match.group(0)
                start = match.start()
                end = match.end()

                # Skip if placeholder is too long or has suspicious content
                if not self._is_valid_placeholder_structure(placeholder_text):
                    continue

                context_before = document_text[max(0, start - 150) : start].strip()
                context_after = document_text[
                    end : min(len(document_text), end + 150)
                ].strip()

                # Step 2: LLM validation (check if it's actually a placeholder)
                confidence = self._validate_placeholder(
                    placeholder_text, context_before, context_after
                )

                if confidence > 0.5:  # Only include if confidence > 50%
                    detections.append(
                        PlaceholderDetection(
                            text=placeholder_text,
                            start_pos=start,
                            end_pos=end,
                            context_before=context_before,
                            context_after=context_after,
                            confidence=confidence,
                        )
                    )

        # Remove duplicates (same position)
        seen_positions = set()
        unique_detections = []
        for detection in detections:
            if detection.start_pos not in seen_positions:
                seen_positions.add(detection.start_pos)
                unique_detections.append(detection)

        return unique_detections

    def _validate_placeholder(
        self, text: str, context_before: str, context_after: str
    ) -> float:
        """Use LLM to validate if detected text is actually a placeholder"""
        prompt = f"""Analyze if the following text is a placeholder that needs to be filled in a legal document.

Detected text: {text}
Context before: {context_before}
Context after: {context_after}

Consider:
- Is it asking for specific information to be filled in?
- Is it a template marker or just regular text in brackets/braces?
- Does the context suggest it needs user input?

Respond with only a confidence score between 0.0 and 1.0, where:
- 1.0 = Definitely a placeholder
- 0.5 = Uncertain
- 0.0 = Definitely not a placeholder

Score:"""

        try:
            response = self.llm.predict(prompt)
            score = float(response.strip())
            return max(0.0, min(1.0, score))  # Clamp between 0 and 1
        except Exception:
            # If LLM fails, use heuristic
            return self._heuristic_confidence(text)

    def _is_valid_placeholder_structure(self, text: str) -> bool:
        """Check if the detected text has a valid placeholder structure"""
        # Remove brackets/braces to check content
        content = re.sub(r"[\[\]{}()<>]", "", text).strip()

        # Reject if too long (likely captured too much text)
        if len(content) > 60:
            return False

        # Reject if contains multiple sentences (has period followed by capital letter)
        if re.search(r"\.\s+[A-Z]", content):
            return False

        # Reject if contains URLs
        if "http://" in content or "https://" in content or ".com" in content:
            return False

        # Reject if contains quotes with long text (likely part of document prose)
        if content.count('"') >= 2 and len(content) > 40:
            return False

        # Reject if it's mostly underscores with text mixed in oddly
        if content.startswith("__]") or content.endswith("[__"):
            return False

        return True

    def _heuristic_confidence(self, text: str) -> float:
        """Fallback heuristic-based confidence scoring"""
        text_lower = text.lower()
        content = re.sub(r"[\[\]{}()<>]", "", text).strip()

        # High confidence indicators
        if any(
            word in text_lower
            for word in [
                "name",
                "date",
                "address",
                "phone",
                "email",
                "state",
                "company",
            ]
        ):
            return 0.9

        # Medium confidence indicators
        if any(word in text_lower for word in ["insert", "fill", "enter", "provide"]):
            return 0.7

        # Blank placeholders [___] are high confidence
        if re.match(r"^[\[{<]+_+[\]}>]+$", text):
            return 0.9

        # Low confidence - but still a bracket/brace pattern
        return 0.6

    async def _arun(self, document_text: str) -> List[PlaceholderDetection]:
        """Async version - not implemented"""
        raise NotImplementedError("Async not supported")
