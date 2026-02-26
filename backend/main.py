"""FastAPI application entry-point for the SolidWorks Semantic Engine.

Start with:
    uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.ollama_backend import OllamaBackend
from backend.routes import generate, parameters, reference

logger = logging.getLogger("sw_semantic_engine")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup / shutdown resources."""

    # -- Startup ----------------------------------------------------------
    model = os.environ.get("SWSE_MODEL", "sw-semantic-7b")
    ollama_url = os.environ.get("SWSE_OLLAMA_URL", "http://localhost:11434")
    backend = OllamaBackend(model_name=model, base_url=ollama_url)
    app.state.ollama = backend

    available = await backend.check_availability()
    if available:
        logger.info(
            "[OK] Ollama backend is reachable (model=%s)", backend.model_name
        )
    else:
        logger.warning(
            "[WARN] Ollama backend is NOT reachable at %s -- "
            "code generation will be unavailable until the server starts.",
            backend.base_url,
        )

    yield

    # -- Shutdown ---------------------------------------------------------
    logger.info("[->] Shutting down Ollama HTTP client...")
    await backend.aclose()
    logger.info("[OK] Shutdown complete.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SolidWorks Semantic Engine",
    version="0.1.0",
    description=(
        "AI-powered SolidWorks API code generation, reference lookup, "
        "and parameterization engine."
    ),
    lifespan=lifespan,
)

# -- CORS (allow local dev front-ends) ------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Routers ---------------------------------------------------------------
app.include_router(generate.router)
app.include_router(reference.router)
app.include_router(parameters.router)


# ---------------------------------------------------------------------------
# Root / health endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    """Landing probe -- confirms the API is running."""
    return {
        "service": "SolidWorks Semantic Engine",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health", tags=["meta"])
async def health() -> dict[str, object]:
    """Health-check endpoint.

    Reports overall service health and Ollama backend availability.
    """
    ollama: OllamaBackend = app.state.ollama
    ollama_ok = await ollama.check_availability()

    return {
        "status": "healthy" if ollama_ok else "degraded",
        "ollama_available": ollama_ok,
        "model": ollama.model_name,
    }
