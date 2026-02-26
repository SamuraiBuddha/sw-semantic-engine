"""Pydantic v2 models for the SolidWorks Semantic Engine API.

Defines request/response schemas for code generation, API reference
lookup, and parameter resolution endpoints.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Code Generation
# ---------------------------------------------------------------------------

class CodeGenerationRequest(BaseModel):
    """Request payload for the /api/generate-code endpoint."""

    prompt: str = Field(
        ...,
        description="Natural-language description of the desired SolidWorks operation.",
    )
    context: str = Field(
        default="",
        description="Optional surrounding code or conversation context.",
    )
    domain: Literal["api", "sketch", "gdt", "feature"] = Field(
        default="api",
        description="Target domain that influences prompt engineering.",
    )
    include_comments: bool = Field(
        default=True,
        description="Whether the generated code should contain inline comments.",
    )
    model: str | None = Field(
        default=None,
        description="Optional model name override. When set, uses this model instead of the server default.",
    )


class CodeGenerationResponse(BaseModel):
    """Response payload returned by the code-generation endpoint."""

    code: str = Field(
        ...,
        description="Generated SolidWorks API code (VBA / C# / Python COM).",
    )
    explanation: str = Field(
        ...,
        description="Human-readable explanation of what the code does.",
    )
    parameters_used: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Parameters that were resolved during generation.",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Model confidence score (0.0 - 1.0).",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings about the generated code.",
    )


# ---------------------------------------------------------------------------
# API Reference
# ---------------------------------------------------------------------------

class APIReferenceResponse(BaseModel):
    """Single SolidWorks API method reference entry."""

    method_name: str = Field(..., description="Name of the API method.")
    interface: str = Field(..., description="COM interface that exposes this method.")
    signature: str = Field(..., description="Full method signature.")
    parameters: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Ordered list of parameter descriptors.",
    )
    return_type: str = Field(..., description="Return type of the method.")
    description: str = Field(..., description="Prose description of the method.")
    example_code: str = Field(..., description="Short example showing typical usage.")


# ---------------------------------------------------------------------------
# Parameter Resolution
# ---------------------------------------------------------------------------

class ParameterResolveRequest(BaseModel):
    """Request to resolve a named parameter space into executable code."""

    parameter_space_name: str = Field(
        ...,
        description="Registered name of the parameter space (e.g. 'extrusion_depth').",
    )
    assignments: dict[str, Any] = Field(
        default_factory=dict,
        description="Mapping of parameter names to concrete values.",
    )


class ParameterResolveResponse(BaseModel):
    """Result of parameter resolution."""

    generated_code: str = Field(
        ...,
        description="Code snippet produced by resolving the parameter space.",
    )
    parameter_space: str = Field(
        ...,
        description="Name of the parameter space that was resolved.",
    )
    assignments_used: dict[str, Any] = Field(
        default_factory=dict,
        description="Final parameter assignments (including defaults).",
    )
    validation_errors: list[str] = Field(
        default_factory=list,
        description="Validation issues encountered during resolution.",
    )
