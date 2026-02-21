"""Code-generation endpoint.

POST /api/generate-code -- accepts a natural-language prompt and returns
generated SolidWorks API code via the Ollama backend.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from backend.models import CodeGenerationRequest, CodeGenerationResponse
from backend.ollama_backend import OllamaBackend

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["generation"])


@router.post(
    "/generate-code",
    response_model=CodeGenerationResponse,
    summary="Generate SolidWorks API code from a natural-language prompt",
)
async def generate_code(
    body: CodeGenerationRequest,
    request: Request,
) -> CodeGenerationResponse:
    """Generate SolidWorks API code.

    The request *domain* selects a specialised system prompt
    (api | sketch | gdt | feature) to guide the model.

    Returns:
        CodeGenerationResponse with the generated code, explanation,
        confidence score, and any warnings.

    Raises:
        HTTPException 503: If the Ollama backend is unreachable.
    """
    ollama: OllamaBackend = request.app.state.ollama

    if not await ollama.check_availability():
        raise HTTPException(
            status_code=503,
            detail=(
                "Ollama backend is not available. "
                "Please ensure the Ollama server is running at "
                f"{ollama.base_url} with model '{ollama.model_name}'."
            ),
        )

    logger.info(
        "[->] Generating code  domain=%s  prompt=%s",
        body.domain,
        body.prompt[:80],
    )

    try:
        response = await ollama.generate_code(body)
    except Exception as exc:
        logger.error("[FAIL] Code generation failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail=f"Code generation failed: {exc}",
        ) from exc

    logger.info(
        "[OK] Code generated  confidence=%.3f  warnings=%d",
        response.confidence,
        len(response.warnings),
    )
    return response
