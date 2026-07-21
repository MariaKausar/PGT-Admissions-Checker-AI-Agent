"""FastAPI application: document upload + assessment + agent chat."""
from __future__ import annotations

import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.agent.admissions_agent import chat as agent_chat
from app.config import get_settings
from app.models.schemas import (
    AssessmentResult,
    ChatRequest,
    ChatResponse,
    ExtractedApplication,
)
from app.services.assessment import assess_application
from app.services.criteria import COURSES, valid_intakes
from app.services.document_parser import UploadedFile, extract_application

settings = get_settings()

app = FastAPI(title="Salford PGT Admissions — Staff Portal", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "model": settings.anthropic_model,
        "api_key_configured": bool(settings.anthropic_api_key),
    }


@app.get("/api/courses")
def courses() -> dict:
    return {
        "courses": [
            {
                "name": c.name,
                "admission_code": c.admission_code,
                "min_classification": c.min_uk_classification,
                "requirement": c.subject_rule.description,
                "intake_months": list(c.valid_months),
                "english": "IELTS 6.0 overall, no band below 5.5 (waived for majority English-speaking countries).",
            }
            for c in COURSES.values()
        ],
        "open_intakes": [f"{o['month']} {o['year']}" for o in valid_intakes(settings.intake_years_ahead)],
    }


@app.post("/api/extract", response_model=ExtractedApplication)
async def extract(files: list[UploadFile] = File(...)) -> ExtractedApplication:
    """Read uploaded PDFs/JPGs with Claude and return the extracted structured data."""
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY is not configured on the server.")
    uploaded = [UploadedFile(f.filename or "file", f.content_type or "", await f.read()) for f in files]
    try:
        return extract_application(uploaded)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Extraction failed: {exc}") from exc


@app.post("/api/assess", response_model=AssessmentResult)
async def assess(files: list[UploadFile] = File(...)) -> AssessmentResult:
    """Full pipeline: read documents, then run the deterministic assessment."""
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY is not configured on the server.")
    uploaded = [UploadedFile(f.filename or "file", f.content_type or "", await f.read()) for f in files]
    try:
        extracted = extract_application(uploaded)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Extraction failed: {exc}") from exc
    return assess_application(extracted)


@app.post("/api/assess-json", response_model=AssessmentResult)
def assess_json(extracted: ExtractedApplication) -> AssessmentResult:
    """Assess an already-extracted application (useful for demos/tests without uploads)."""
    return assess_application(extracted)


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY is not configured on the server.")
    session_id = req.session_id or str(uuid.uuid4())
    try:
        reply = agent_chat(req.message, session_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc
    return ChatResponse(reply=reply, session_id=session_id)
