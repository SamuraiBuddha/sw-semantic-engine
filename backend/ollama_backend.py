"""Ollama integration backend for SolidWorks code generation.

Communicates with a local Ollama instance running the sw-semantic-7b
model (or any compatible model) to produce SolidWorks API code from
natural-language prompts.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from backend.models import CodeGenerationRequest, CodeGenerationResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain-specific system prompts
# ---------------------------------------------------------------------------

_DOMAIN_PROMPTS: dict[str, str] = {
    "api": (
        "You are a SolidWorks API expert. Generate precise SolidWorks API "
        "code using the official COM interfaces (ISldWorks, IModelDoc2, "
        "IFeatureManager, etc.). Always use correct method signatures and "
        "parameter types. Prefer early-bound references where possible."
    ),
    "sketch": (
        "You are a SolidWorks Sketch specialist. Generate code that creates "
        "and manipulates 2D sketches via ISketchManager and ISketchSegment. "
        "Include proper sketch enter/exit calls (InsertSketch), dimension "
        "constraints, and geometric relations."
    ),
    "gdt": (
        "You are a GD&T (Geometric Dimensioning and Tolerancing) expert for "
        "SolidWorks. Generate code that applies DimXpert annotations, "
        "tolerance features, datum references, and inspection dimensions "
        "using the IDimXpertManager and related interfaces."
    ),
    "feature": (
        "You are a SolidWorks Feature-Tree expert. Generate code that "
        "creates and edits features via IFeatureManager -- extrusions, "
        "revolves, cuts, fillets, chamfers, patterns, and boolean "
        "operations. Use correct enum values for end conditions."
    ),
}


class OllamaBackend:
    """Async wrapper around the Ollama REST API for SolidWorks code generation."""

    def __init__(
        self,
        model_name: str = "sw-semantic-7b",
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
        )

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    async def check_availability(self) -> bool:
        """Return True if the Ollama server is reachable and responsive."""
        try:
            resp = await self._client.get("/api/tags")
            return resp.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    async def generate_code(
        self,
        request: CodeGenerationRequest,
    ) -> CodeGenerationResponse:
        """Send a generation request to Ollama and parse the result.

        Args:
            request: Validated code-generation request.

        Returns:
            A ``CodeGenerationResponse`` with extracted code, explanation,
            and metadata.

        Raises:
            httpx.HTTPStatusError: If Ollama returns a non-2xx status.
        """
        # Use per-request model override if provided, otherwise fall back to default
        model = request.model or self.model_name

        system_prompt = self._build_system_prompt(request.domain)

        user_message = request.prompt
        if request.context:
            user_message = f"Context:\n{request.context}\n\nRequest:\n{user_message}"
        if request.include_comments:
            user_message += "\n\nInclude descriptive inline comments in the code."

        payload: dict[str, Any] = {
            "model": model,
            "prompt": user_message,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
            },
        }

        resp = await self._client.post("/api/generate", json=payload)
        resp.raise_for_status()

        data = resp.json()
        raw_response: str = data.get("response", "")

        code, explanation = self._extract_code_from_response(raw_response)

        warnings: list[str] = []
        if not code:
            warnings.append("No code block detected in model response.")

        # Rough confidence heuristic based on response length and code presence.
        confidence = min(1.0, 0.3 + 0.4 * bool(code) + 0.3 * min(len(code) / 200, 1.0))

        return CodeGenerationResponse(
            code=code,
            explanation=explanation,
            parameters_used=[],
            confidence=round(confidence, 3),
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_system_prompt(self, domain: str) -> str:
        """Return the system prompt for the given *domain*.

        Falls back to the generic ``api`` prompt for unknown domains.
        """
        return _DOMAIN_PROMPTS.get(domain, _DOMAIN_PROMPTS["api"])

    @staticmethod
    def _extract_code_from_response(raw: str) -> tuple[str, str]:
        """Split the raw LLM output into (code, explanation).

        Looks for fenced code blocks (```...```) first.  If none are found
        the entire response is treated as explanation with an empty code
        string.
        """
        # Try to extract fenced code blocks.
        pattern = r"```(?:\w+)?\s*\n(.*?)```"
        matches = re.findall(pattern, raw, re.DOTALL)

        if matches:
            code = "\n\n".join(m.strip() for m in matches)
            # Everything outside the code fences is the explanation.
            explanation = re.sub(pattern, "", raw, flags=re.DOTALL).strip()
            return code, explanation

        # No fenced block -- return the whole thing as explanation.
        return "", raw.strip()

    async def aclose(self) -> None:
        """Gracefully close the underlying HTTP client."""
        await self._client.aclose()
