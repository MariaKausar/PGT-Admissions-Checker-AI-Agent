"""Read applicant PDFs / JPGs with LangChain + Claude (multimodal vision)."""
from __future__ import annotations

import base64
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage

from app.models.schemas import ExtractedApplication
from app.services.llm import get_llm

EXTRACTION_SYSTEM_PROMPT = """You are an admissions document reader for the University of Salford PGT team.

Applicants submit documents in PDF or JPG format. Per the admissions process, identify which of
these THREE document types are present and extract their data:

DOCUMENT 1 — PGT course choice sheet (structured format):
  Course: <name>          e.g. Artificial Intelligence
  Code: <admission code>  e.g. i403T
  Year of Entry: <year>   e.g. 2026
  Month of Entry: <month> e.g. September

DOCUMENT 2 — Formal degree certificate:
  Degree title, subject, awarding institution, country, UK classification if stated.

DOCUMENT 3 — Academic transcript:
  List of modules/subjects studied with grades, plus overall percentage or CGPA (with scale).

Set `documents_provided` to show which of the three types you actually saw:
  - course_choice: true if Document 1 is present
  - degree_certificate: true if Document 2 is present
  - transcript: true if Document 3 is present

Grade reading order:
  1. Identify `awarding_country` (country where degree was awarded).
  2. Read grading system: percentage and/or CGPA with scale (4, 5, or 10).
  3. Record achieved marks.

Rules:
- Only report values you can see. Leave fields null if not present.
- Report `cgpa` AND `cgpa_scale` together when CGPA is shown.
- English tests (IELTS, PTE, TOEFL, etc.): fill `ielts` or `english_qualification` if a test report is uploaded.
- Put ambiguities in `extraction_notes`.
Return ONLY structured data."""


@dataclass
class UploadedFile:
    filename: str
    content_type: str
    data: bytes


def _media_type_for(file: UploadedFile) -> str:
    ct = (file.content_type or "").lower()
    name = file.filename.lower()
    if "pdf" in ct or name.endswith(".pdf"):
        return "application/pdf"
    if name.endswith(".png") or "png" in ct:
        return "image/png"
    if name.endswith(".webp") or "webp" in ct:
        return "image/webp"
    if name.endswith(".gif") or "gif" in ct:
        return "image/gif"
    return "image/jpeg"


def _content_block(file: UploadedFile) -> dict:
    media_type = _media_type_for(file)
    b64 = base64.standard_b64encode(file.data).decode("utf-8")
    block_type = "document" if media_type == "application/pdf" else "image"
    return {
        "type": block_type,
        "source": {"type": "base64", "media_type": media_type, "data": b64},
    }


def extract_application(files: list[UploadedFile]) -> ExtractedApplication:
    """Run the multimodal extraction over all uploaded files at once."""
    if not files:
        return ExtractedApplication(extraction_notes="No documents were uploaded.")

    llm = get_llm()
    structured_llm = llm.with_structured_output(ExtractedApplication)

    content: list[dict] = [
        {
            "type": "text",
            "text": (
                "Here are all documents for one applicant. Identify which of the three "
                "required document types are present and return consolidated structured data."
            ),
        }
    ]
    for f in files:
        content.append({"type": "text", "text": f"--- Document: {f.filename} ---"})
        content.append(_content_block(f))

    messages = [
        SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
        HumanMessage(content=content),
    ]

    result = structured_llm.invoke(messages)
    return result  # type: ignore[return-value]
