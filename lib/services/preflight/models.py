from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ValidationSeverity(str, Enum):
    """Severity level of a validation issue."""

    ERROR = "error"
    WARNING = "warning"


class ValidationIssue(BaseModel):
    """A single validation issue found during preflight check."""

    code: str = Field(description="Machine-readable issue code")
    message: str = Field(description="Human-readable description")
    severity: ValidationSeverity = Field(default=ValidationSeverity.ERROR)
    details: dict[str, Any] | None = Field(default=None)


class PreflightResult(BaseModel):
    """Result of running all preflight validators."""

    valid: bool = Field(description="True if no errors (warnings allowed)")
    issues: list[ValidationIssue] = Field(default_factory=list)


class PreflightRequest(BaseModel):
    """Request context for preflight validation."""

    openai_api_key: str | None = Field(
        default=None, description="User-provided OpenAI API key to validate"
    )
