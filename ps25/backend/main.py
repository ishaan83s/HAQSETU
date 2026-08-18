import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("backend")

# Ensure repository root and model directory are in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
PS25_DIR = BACKEND_DIR.parent
PROJECT_ROOT = PS25_DIR.parent
MODEL_DIR = PS25_DIR / "model"

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PS25_DIR / ".env")

for p in [str(PROJECT_ROOT), str(PS25_DIR), str(MODEL_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Set fallback COE_API_KEY for module import safety if not configured yet
os.environ.setdefault("COE_API_KEY", "dummy-coe-key-for-startup")

# Direct import of existing RAG answer_query function
from src.rag import answer_query

app = FastAPI(
    title="HAQSETU Legal RAG Backend",
    description="FastAPI backend adapter sitting between the existing React frontend and RAG ML pipeline.",
    version="1.0.0"
)

# Configure CORS for frontend development
cors_origins_env = os.getenv("CORS_ORIGINS", "")
allowed_origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
for origin in default_origins:
    if origin not in allowed_origins:
        allowed_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for incidents and user session context
incidents_store: dict[str, dict] = {}
user_contexts_store: dict[str, dict] = {}


# --- Canonical Schemas ---
class HealthResponse(BaseModel):
    status: str = Field(default="ok")


class AskRequest(BaseModel):
    query: str = Field(..., description="User query string")


class AskResponse(BaseModel):
    answer: str = Field(..., description="RAG generated answer")
    sources: list[str] = Field(default_factory=list, description="Source legal citations")


# --- Frontend Adapter Schemas ---
class RequestOtpRequest(BaseModel):
    phoneNumber: str


class VerifyOtpRequest(BaseModel):
    phoneNumber: str
    otp: str


class UserContextRequest(BaseModel):
    state: Optional[str] = None
    roleCategory: Optional[str] = None
    vulnerabilityTags: Optional[List[str]] = None


class CreateIncidentRequest(BaseModel):
    inputMode: str = Field(default="text")
    language: str = Field(default="en")
    text: Optional[str] = None
    audioBase64: Optional[str] = None


# --- Canonical Endpoints ---
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


# --- Frontend Adapter Endpoints ---
@app.post("/auth/request-otp")
async def auth_request_otp(payload: RequestOtpRequest):
    clean_digits = "".join(filter(str.isdigit, payload.phoneNumber))
    if len(clean_digits) < 10:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": "INVALID_PHONE",
                    "message": "Please enter a valid 10-digit mobile number."
                }
            }
        )
    return {
        "success": True,
        "data": {
            "otpSent": True
        },
        "error": None
    }


@app.post("/auth/verify-otp")
async def auth_verify_otp(payload: VerifyOtpRequest):
    clean_otp = payload.otp.strip()
    if len(clean_otp) != 6 or not clean_otp.isdigit():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": "INVALID_OTP",
                    "message": "Please enter a valid 6-digit OTP code."
                }
            }
        )
    
    mock_otp = os.getenv("MOCK_OTP", "123456")
    if clean_otp != mock_otp and clean_otp != "123456":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": "INVALID_OTP",
                    "message": "Invalid OTP code. Please try again."
                }
            }
        )

    user_id = f"usr_{uuid.uuid4().hex[:8]}"
    token = f"ps25_token_{uuid.uuid4().hex[:16]}"
    return {
        "success": True,
        "data": {
            "token": token,
            "userId": user_id
        },
        "error": None
    }


@app.put("/users/context")
async def update_user_context(payload: UserContextRequest):
    # Store context safely in memory without changing the ML pipeline
    user_contexts_store["current_user"] = payload.model_dump()
    return {
        "success": True,
        "data": {
            "saved": True
        },
        "error": None
    }


@app.post("/incidents")
async def create_incident(payload: CreateIncidentRequest):
    if payload.inputMode == "voice":
        # ML pipeline currently accepts text only. Return emptyTranscription flag for clear fallback.
        return {
            "success": True,
            "data": {
                "emptyTranscription": True
            },
            "error": None
        }

    query_text = (payload.text or "").strip()
    if not query_text:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": "EMPTY_TEXT",
                    "message": "Please describe what happened."
                }
            }
        )

    try:
        # Execute the real RAG ML pipeline
        result = await run_in_threadpool(answer_query, query_text)
        answer = result.get("answer", "")
        sources = result.get("sources", [])

        incident_id = uuid.uuid4().hex[:12]

        # Map sources into official resources structure expected by frontend
        official_resources = []
        for src in list(dict.fromkeys(sources)):  # preserve order & deduplicate
            official_resources.append({
                "text": f"Referenced in {src}",
                "source": {
                    "title": src,
                    "section": None,
                    "jurisdictionState": None,
                    "sourceUrl": "https://www.indiacode.nic.in/",
                    "effectiveDate": None,
                    "versionLabel": None
                }
            })

        incident_data = {
            "incidentId": incident_id,
            "triage": {
                "issues": [{"type": "Legal Awareness"}],
                "actor": None,
                "jurisdictionState": None,
                "urgency": "general",
                "cards": {
                    "whatMayBeHappening": {
                        "text": answer
                    },
                    "whatMayProtectYou": official_resources,
                    "evidenceToKeep": [],
                    "whatYouCanDoNext": [],
                    "legalAid": {
                        "name": "National Legal Services Authority (NALSA)",
                        "contactInfo": "Toll-Free Helpline: 15100 | https://nalsa.gov.in"
                    }
                }
            }
        }

        # Cache incident for subsequent GET /incidents/{incidentId} request
        incidents_store[incident_id] = incident_data

        return {
            "success": True,
            "data": incident_data,
            "error": None
        }
    except Exception as exc:
        logger.exception("Error during RAG execution: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": "AI_SERVICE_ERROR",
                    "message": "AI service temporarily unavailable. Please try again later."
                }
            }
        )


@app.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    if incident_id not in incidents_store:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Incident #{incident_id} not found."
                }
            }
        )

    return {
        "success": True,
        "data": incidents_store[incident_id],
        "error": None
    }
