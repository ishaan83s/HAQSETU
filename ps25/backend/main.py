import logging
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("backend")

# Ensure repository root containing 'src' is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
MODEL_ROOT_DIR = BACKEND_DIR.parent

if str(MODEL_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT_DIR))

# Direct import of existing RAG answer_query function.
# Fails clearly at startup if environment or module dependencies are missing.
from src.rag import answer_query

app = FastAPI(
    title="Legal RAG API Backend",
    description="FastAPI backend wrapping existing RAG model service.",
    version="1.0.0"
)


class HealthResponse(BaseModel):
    status: str = Field(default="ok")


class AskRequest(BaseModel):
    query: str = Field(..., description="User query string")


class AskResponse(BaseModel):
    answer: str = Field(..., description="RAG generated answer")
    sources: list[str] = Field(default_factory=list, description="Source legal citations")


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    # Reject empty or whitespace-only queries
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty or whitespace-only."
        )

    try:
        # Call synchronous RAG function using starlette threadpool mechanism
        result = await run_in_threadpool(answer_query, request.query.strip())
        
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        
        return AskResponse(answer=answer, sources=sources)
    except Exception as exc:
        logger.exception("Error during RAG execution: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service temporarily unavailable."
        )
