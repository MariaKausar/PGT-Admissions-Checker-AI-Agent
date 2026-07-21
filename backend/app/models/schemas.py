"""Pydantic schemas shared across the API and the agent."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Decision(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    REVIEW = "REVIEW"  # borderline / manual review needed
    INCOMPLETE = "INCOMPLETE"  # required documents/evidence missing — request more


class IeltsScores(BaseModel):
    """IELTS band scores. Any field may be missing if not supplied by the applicant."""

    overall: Optional[float] = None
    listening: Optional[float] = None
    reading: Optional[float] = None
    writing: Optional[float] = None
    speaking: Optional[float] = None


class EnglishQualification(BaseModel):
    """An accepted English test other than IELTS (PTE, TOEFL iBT, LanguageCert, Trinity ISE)."""

    test_type: Optional[str] = None       # e.g. "PTE Academic", "TOEFL iBT", "LanguageCert", "Trinity ISE"
    overall: Optional[float] = None
    lowest_component: Optional[float] = None  # lowest sub-skill score if shown


class TranscriptModule(BaseModel):
    name: str
    grade: Optional[str] = None


class DocumentsProvided(BaseModel):
    """Which of the three applicant document types from the candidate brief were seen."""

    course_choice: bool = False       # Course, Code, Year of Entry, Month of Entry
    degree_certificate: bool = False  # Formal degree certificate
    transcript: bool = False          # Transcript with modules and grades


class ExtractedApplication(BaseModel):
    """Structured data extracted from the applicant's uploaded documents."""

    applicant_name: Optional[str] = None

    # From the structured "course choice" document
    course_name: Optional[str] = None
    admission_code: Optional[str] = None
    year_of_entry: Optional[int] = None
    month_of_entry: Optional[str] = None

    # From the degree certificate + transcript
    degree_title: Optional[str] = None
    degree_subject: Optional[str] = None
    awarding_country: Optional[str] = None
    uk_classification: Optional[str] = None  # e.g. "2:2" if stated on a UK-style certificate
    percentage: Optional[float] = None       # e.g. 62.5
    cgpa: Optional[float] = None             # e.g. 6.8
    cgpa_scale: Optional[float] = None       # e.g. 10 or 4

    # English language
    first_language_english: Optional[bool] = None
    ielts: Optional[IeltsScores] = None
    english_qualification: Optional[EnglishQualification] = None

    modules: list[TranscriptModule] = Field(default_factory=list)

    # Which document types were identified in the upload (candidate brief)
    documents_provided: Optional[DocumentsProvided] = None

    extraction_notes: Optional[str] = None


class CheckResult(BaseModel):
    """The outcome of a single entrance-requirement check."""

    name: str
    passed: Optional[bool] = None  # None => could not determine
    detail: str


class AssessmentResult(BaseModel):
    decision: Decision
    course_matched: Optional[str] = None
    checks: list[CheckResult] = Field(default_factory=list)
    summary: str
    confidence: Optional[str] = None
    extracted: Optional[ExtractedApplication] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
