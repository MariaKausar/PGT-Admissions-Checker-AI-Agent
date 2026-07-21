"""Deterministic assessment engine aligned to the candidate brief.

Flow (per SME brief):
  1. Confirm the three applicant document types are present:
       - PGT course choice (Course, Code, Year of Entry, Month of Entry)
       - Formal degree certificate
       - Academic transcript (modules and grades)
  2. Match course (MSc AI / Data Science / Software Engineering)
  3. Check course-specific entrance criteria
  4. Return ACCEPT / REJECT / REVIEW / INCOMPLETE (request missing documents)
"""
from __future__ import annotations

from app.config import get_settings
from app.models.schemas import (
    AssessmentResult,
    CheckResult,
    Decision,
    DocumentsProvided,
    ExtractedApplication,
)
from app.services import criteria as crit
from app.services import country_rules as cr


def assess_application(extracted: ExtractedApplication) -> AssessmentResult:
    settings = get_settings()
    checks: list[CheckResult] = []

    # --- Step 1: Required documents (candidate brief) ---
    docs = _resolve_documents(extracted)
    missing_docs = _missing_documents(extracted, docs)

    if missing_docs:
        checks.append(CheckResult(
            name="Required documents (brief)",
            passed=None,
            detail="Missing: " + "; ".join(missing_docs),
        ))
        for label, present in [
            ("1. PGT course choice sheet", docs.course_choice),
            ("2. Degree certificate", docs.degree_certificate),
            ("3. Academic transcript", docs.transcript),
        ]:
            checks.append(CheckResult(
                name=label,
                passed=True if present else None,
                detail="Provided" if present else "Not found in upload",
            ))
        return AssessmentResult(
            decision=Decision.INCOMPLETE,
            course_matched=extracted.course_name,
            checks=checks,
            summary=(
                "Cannot assess this application yet — not all required documents were uploaded. "
                f"Please request: {'; '.join(missing_docs)}."
            ),
            confidence="n/a",
            extracted=extracted,
        )

    checks.append(CheckResult(
        name="Required documents (brief)",
        passed=True,
        detail="All three document types present: course choice sheet, degree certificate, and transcript.",
    ))

    # --- Step 2: Match course ---
    course = crit.find_course(extracted.course_name, extracted.admission_code)
    if course is None:
        checks.append(CheckResult(
            name="Course match",
            passed=False,
            detail=(
                f"Could not match course '{extracted.course_name or 'unknown'}' "
                f"(code: {extracted.admission_code or 'n/a'}). "
                "Supported: MSc Artificial Intelligence (i403T), MSc Data Science (i402T), "
                "MSc Software Engineering (i404T)."
            ),
        ))
        return AssessmentResult(
            decision=Decision.REVIEW,
            course_matched=None,
            checks=checks,
            summary="Course on the application form could not be matched. Route to admissions staff.",
            confidence="low",
            extracted=extracted,
        )

    checks.append(CheckResult(
        name="Course match",
        passed=True,
        detail=f"Matched to {course.name} (code {course.admission_code}).",
    ))

    # --- Step 3: Course-specific entrance criteria ---

    # 3a) Entry date (dynamic, course-specific months).
    intake_ok, intake_detail = crit.is_valid_intake(
        extracted.month_of_entry,
        extracted.year_of_entry,
        years_ahead=settings.intake_years_ahead,
        course=course,
    )
    checks.append(CheckResult(name="Entry date (intake)", passed=intake_ok, detail=intake_detail))

    # 3b) Degree grade — country first, then grading system, then marks.
    grade_eval = cr.evaluate_degree_grade(
        country=extracted.awarding_country,
        percentage=extracted.percentage,
        cgpa=extracted.cgpa,
        cgpa_scale=extracted.cgpa_scale,
        uk_classification=extracted.uk_classification,
    )
    grade_detail = grade_eval.detail
    if grade_eval.borderline:
        grade_detail += " (borderline — recommend manual review)"
    checks.append(CheckResult(
        name=f"Degree grade (min {course.min_uk_classification})",
        passed=grade_eval.meets_2_2,
        detail=grade_detail,
    ))

    # 3c) Subject relevance — DIFFERENT per course (key brief requirement).
    module_names = [m.name for m in extracted.modules] if extracted.modules else []
    subj_eval = crit.evaluate_subject(course, extracted.degree_subject, extracted.degree_title, module_names)
    subject_label = _subject_check_label(course)
    checks.append(CheckResult(name=subject_label, passed=subj_eval.passed, detail=subj_eval.detail))

    # 3d) English language (Salford requirements page).
    english_check = _english_check(extracted)
    checks.append(english_check)

    # --- Step 4: Combine into decision ---
    decision, summary, confidence = _combine(course, checks, grade_eval.borderline)

    return AssessmentResult(
        decision=decision,
        course_matched=course.name,
        checks=checks,
        summary=summary,
        confidence=confidence,
        extracted=extracted,
    )


def _subject_check_label(course: crit.Course) -> str:
    if course.key == "data science":
        return "Mathematical aptitude (Data Science)"
    if course.key == "artificial intelligence":
        return "CS/STEM + programming (Artificial Intelligence)"
    if course.key == "software engineering":
        return "CS/STEM + programming (Software Engineering)"
    return "Subject relevance"


def _resolve_documents(extracted: ExtractedApplication) -> DocumentsProvided:
    """Infer which of the three brief document types were provided."""
    declared = extracted.documents_provided

    course_choice = bool(
        (declared and declared.course_choice)
        or (extracted.course_name and extracted.admission_code and extracted.year_of_entry and extracted.month_of_entry)
    )
    degree_certificate = bool(
        (declared and declared.degree_certificate)
        or extracted.degree_title
        or extracted.uk_classification
    )
    transcript = bool(
        (declared and declared.transcript)
        or extracted.modules
        or extracted.percentage is not None
        or extracted.cgpa is not None
    )
    return DocumentsProvided(
        course_choice=course_choice,
        degree_certificate=degree_certificate,
        transcript=transcript,
    )


def _missing_documents(extracted: ExtractedApplication, docs: DocumentsProvided) -> list[str]:
    """Per candidate brief — all three document types must be present before assessing."""
    missing: list[str] = []

    if not docs.course_choice:
        missing.append(
            "PGT course choice sheet (Course, Code, Year of Entry, Month of Entry) "
            "e.g. Course: Artificial Intelligence, Code: i403T, Year: 2026, Month: September"
        )
    if not docs.degree_certificate:
        missing.append("Formal degree certificate (degree title, awarding institution, country)")
    if not docs.transcript:
        missing.append("Academic transcript listing modules/subjects studied and grades")

    # English — additional requirement if not exempt (not one of the 3 brief docs, but required by Salford).
    exempt = extracted.first_language_english is True or cr.is_majority_english_speaking(extracted.awarding_country)
    has_english = (
        (extracted.ielts is not None and extracted.ielts.overall is not None)
        or (extracted.english_qualification is not None and extracted.english_qualification.overall is not None)
    )
    if not exempt and not has_english and docs.degree_certificate:
        missing.append(
            "English language evidence — IELTS Academic 6.0 (no band below 5.5) or accepted equivalent "
            "(PTE Academic, TOEFL iBT, LanguageCert, Trinity ISE) per Salford requirements"
        )

    return missing


def _english_check(extracted: ExtractedApplication) -> CheckResult:
    if extracted.first_language_english is True:
        return CheckResult(
            name="English language",
            passed=True,
            detail="Applicant's first language is English — IELTS not required.",
        )
    if cr.is_majority_english_speaking(extracted.awarding_country):
        return CheckResult(
            name="English language",
            passed=True,
            detail=f"Awarding country '{extracted.awarding_country}' is majority English-speaking — exemption applies.",
        )

    ielts_eval = crit.evaluate_ielts(extracted.ielts)
    if ielts_eval.passed is not None:
        return CheckResult(name="English language", passed=ielts_eval.passed, detail=ielts_eval.detail)

    alt_eval = crit.evaluate_english_qualification(extracted.english_qualification)
    if alt_eval.passed is not None:
        return CheckResult(name="English language", passed=alt_eval.passed, detail=alt_eval.detail)

    return CheckResult(
        name="English language",
        passed=None,
        detail="English evidence required but not provided.",
    )


def _combine(course, checks: list[CheckResult], grade_borderline: bool) -> tuple[Decision, str, str]:
    substantive = [c for c in checks if c.name not in ("Required documents (brief)", "Course match")]

    failed = [c for c in substantive if c.passed is False]
    unknown = [c for c in substantive if c.passed is None]
    passed = [c.name for c in substantive if c.passed is True]

    if failed:
        return (
            Decision.REJECT,
            f"Does not meet entrance requirements for {course.name}. Failed: {', '.join(c.name for c in failed)}.",
            "high",
        )
    if unknown:
        return (
            Decision.REVIEW,
            f"Potentially eligible for {course.name} but needs manual review: {', '.join(c.name for c in unknown)}.",
            "medium",
        )
    if grade_borderline:
        return (
            Decision.REVIEW,
            f"All criteria appear met for {course.name}, but the degree grade is borderline — human check recommended.",
            "medium",
        )
    return (
        Decision.ACCEPT,
        f"Meets all entrance requirements for {course.name}: {', '.join(passed)}.",
        "high",
    )
