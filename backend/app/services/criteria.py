"""Course entrance criteria, dynamic intake generation, IELTS and subject checks.

Criteria verified against the University of Salford course pages (2026 entry):
  - MSc Artificial Intelligence: 2:2 hons in CS or a related STEM subject that
    included programming content.
  - MSc Data Science: 2:2 hons in ANY discipline, WITH demonstrable mathematical
    aptitude (e.g. A-level / BTEC Maths or a quantitative degree).
  - MSc Software Engineering: 2:2 hons in CS or a related STEM subject with
    coverage of computer programming.
All three: IELTS 6.0 overall with no element below 5.5 (if English not first language).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from app.models.schemas import IeltsScores

# --------------------------------------------------------------------------------------
# IELTS requirement (shared across all three PGT courses)
# --------------------------------------------------------------------------------------
IELTS_MIN_OVERALL = 6.0
IELTS_MIN_BAND = 5.5


@dataclass
class SubjectRule:
    """Rule describing which degree subjects are acceptable for a course."""

    # If True, any discipline is acceptable at degree level.
    any_discipline: bool = False
    # Keywords that indicate an acceptable subject (used when any_discipline is False).
    acceptable_keywords: list[str] = field(default_factory=list)
    # Whether the course additionally requires demonstrable mathematical aptitude.
    requires_maths_aptitude: bool = False
    # Whether the course requires programming/computing content in the prior degree.
    requires_programming: bool = False
    description: str = ""


@dataclass
class Course:
    key: str
    name: str
    admission_code: str
    min_uk_classification: str  # "2:2"
    subject_rule: SubjectRule
    valid_months: tuple[str, ...] = ("January", "September")


STEM_KEYWORDS = [
    "computer science", "computing", "software", "information technology", "it",
    "artificial intelligence", "data science", "data", "mathematics", "maths",
    "statistics", "engineering", "physics", "electronics", "electrical",
    "science", "technology", "informatics", "machine learning",
]

PROGRAMMING_KEYWORDS = [
    "programming", "software", "computer science", "computing", "python", "java",
    "c++", "coding", "development", "informatics",
]

MATHS_KEYWORDS = [
    "mathematics", "maths", "statistics", "calculus", "algebra", "quantitative",
    "econometrics", "data", "computer science", "engineering", "physics",
]


COURSES: dict[str, Course] = {
    "artificial intelligence": Course(
        key="artificial intelligence",
        name="MSc Artificial Intelligence",
        admission_code="i403T",
        min_uk_classification="2:2",
        subject_rule=SubjectRule(
            acceptable_keywords=STEM_KEYWORDS,
            requires_programming=True,
            description="2:2 honours in Computer Science or a related STEM subject that included programming content.",
        ),
    ),
    "data science": Course(
        key="data science",
        name="MSc Data Science",
        admission_code="i402T",
        min_uk_classification="2:2",
        subject_rule=SubjectRule(
            any_discipline=True,
            requires_maths_aptitude=True,
            description="2:2 honours in any discipline WITH demonstrable mathematical aptitude (e.g. A-level/BTEC Maths or a quantitative degree).",
        ),
    ),
    "software engineering": Course(
        key="software engineering",
        name="MSc Software Engineering",
        admission_code="i404T",
        min_uk_classification="2:2",
        subject_rule=SubjectRule(
            acceptable_keywords=STEM_KEYWORDS,
            requires_programming=True,
            description="2:2 honours in Computer Science or a related STEM subject with coverage of computer programming.",
        ),
        valid_months=("September",),  # Salford course page: September intakes only
    ),
}


def find_course(course_name: Optional[str], admission_code: Optional[str] = None) -> Optional[Course]:
    """Match an applicant's stated course to one of our known courses."""
    if admission_code:
        code = admission_code.strip().lower()
        for c in COURSES.values():
            if c.admission_code.lower() == code:
                return c
    if course_name:
        name = course_name.strip().lower()
        # direct key hit
        if name in COURSES:
            return COURSES[name]
        # fuzzy contains
        for key, c in COURSES.items():
            if key in name or name in key:
                return c
        if "ai" in name.split() or "a.i" in name:
            return COURSES["artificial intelligence"]
    return None


# --------------------------------------------------------------------------------------
# Dynamic intake dates (NOT hardcoded)
# --------------------------------------------------------------------------------------
def valid_intakes(years_ahead: int = 2, today: Optional[date] = None) -> list[dict]:
    """Generate the list of currently-open intakes relative to today's date.

    Salford PGT courses start in January and September. We generate the next
    available intakes so the agent never relies on a hardcoded year.
    """
    today = today or date.today()
    intakes: list[dict] = []
    # Intake reference months
    month_map = {"January": 1, "September": 9}
    for year in range(today.year, today.year + years_ahead + 1):
        for month_name, month_num in month_map.items():
            intake_start = date(year, month_num, 1)
            # Only include intakes that have not already started.
            if intake_start >= date(today.year, today.month, 1):
                intakes.append({"month": month_name, "year": year})
    return intakes


def is_valid_intake(
    month: Optional[str],
    year: Optional[int],
    years_ahead: int = 2,
    today: Optional[date] = None,
    course: Optional[Course] = None,
) -> tuple[Optional[bool], str]:
    if not month or not year:
        return None, "Year and/or month of entry not provided — need the course choice document."

    month_norm = month.strip().capitalize()
    year_int = int(year)

    # Course-specific month check (e.g. Software Engineering is September only).
    if course and month_norm not in course.valid_months:
        allowed = ", ".join(course.valid_months)
        return False, (
            f"{month_norm} is not a valid intake month for {course.name}. "
            f"This course accepts: {allowed}."
        )

    options = valid_intakes(years_ahead=years_ahead, today=today)
    match = {"month": month_norm, "year": year_int}
    if match in options:
        return True, f"{month_norm} {year_int} is an open intake for {course.name if course else 'this course'}."
    pretty = ", ".join(f"{o['month']} {o['year']}" for o in options)
    return False, f"{month_norm} {year_int} is not a currently-open intake. Open intakes: {pretty}."


# --------------------------------------------------------------------------------------
# IELTS check
# --------------------------------------------------------------------------------------
@dataclass
class IeltsEvaluation:
    passed: Optional[bool]
    detail: str


def evaluate_ielts(ielts: Optional[IeltsScores]) -> IeltsEvaluation:
    if ielts is None or ielts.overall is None:
        return IeltsEvaluation(None, "No IELTS scores provided.")

    bands = {
        "listening": ielts.listening,
        "reading": ielts.reading,
        "writing": ielts.writing,
        "speaking": ielts.speaking,
    }

    if ielts.overall < IELTS_MIN_OVERALL:
        return IeltsEvaluation(False, f"Overall IELTS {ielts.overall} is below the required {IELTS_MIN_OVERALL}.")

    low_bands = {k: v for k, v in bands.items() if v is not None and v < IELTS_MIN_BAND}
    if low_bands:
        detail = ", ".join(f"{k} {v}" for k, v in low_bands.items())
        return IeltsEvaluation(False, f"Overall {ielts.overall} is fine, but these bands are below {IELTS_MIN_BAND}: {detail}.")

    missing = [k for k, v in bands.items() if v is None]
    if missing:
        return IeltsEvaluation(
            True,
            f"Overall {ielts.overall} meets {IELTS_MIN_OVERALL} and provided bands are >= {IELTS_MIN_BAND}. "
            f"(Note: no data for {', '.join(missing)} — confirm each band.)",
        )
    return IeltsEvaluation(True, f"Overall {ielts.overall} >= {IELTS_MIN_OVERALL} and all bands >= {IELTS_MIN_BAND}.")


# --------------------------------------------------------------------------------------
# Accepted English alternatives (Salford PGT), per the University English requirements page.
# Each entry: minimum overall, minimum any component.
# --------------------------------------------------------------------------------------
ENGLISH_ALTERNATIVES = {
    "pte": {"label": "PTE Academic", "overall": 59.0, "component": 59.0},
    "toefl": {"label": "TOEFL iBT", "overall": 79.0, "component": 17.0},
    "languagecert": {"label": "LanguageCert Academic", "overall": 33.0, "component": 33.0},
    "trinity": {"label": "Trinity ISE", "overall": None, "component": None},
}


def _match_english_alt(test_type: str) -> Optional[str]:
    t = test_type.lower()
    if "pte" in t or "pearson" in t:
        return "pte"
    if "toefl" in t:
        return "toefl"
    if "languagecert" in t or "language cert" in t:
        return "languagecert"
    if "trinity" in t or "ise" in t:
        return "trinity"
    return None


def evaluate_english_qualification(qual) -> IeltsEvaluation:
    """Evaluate a non-IELTS accepted English test."""
    if qual is None or not qual.test_type or qual.overall is None:
        return IeltsEvaluation(None, "No recognised English test scores provided.")
    key = _match_english_alt(qual.test_type)
    if key is None:
        return IeltsEvaluation(
            None,
            f"'{qual.test_type}' is not a recognised Salford English qualification — refer to admissions.",
        )
    req = ENGLISH_ALTERNATIVES[key]
    if req["overall"] is None:
        return IeltsEvaluation(None, f"{req['label']} provided — confirm score against Salford requirements.")
    if qual.overall < req["overall"]:
        return IeltsEvaluation(False, f"{req['label']} {qual.overall} is below the required {req['overall']:g}.")
    if qual.lowest_component is not None and req["component"] and qual.lowest_component < req["component"]:
        return IeltsEvaluation(
            False,
            f"{req['label']} overall {qual.overall} is fine, but a component ({qual.lowest_component:g}) "
            f"is below the required {req['component']:g}.",
        )
    return IeltsEvaluation(True, f"{req['label']} {qual.overall} meets the requirement ({req['overall']:g}).")


# --------------------------------------------------------------------------------------
# Subject relevance check
# --------------------------------------------------------------------------------------
@dataclass
class SubjectEvaluation:
    passed: Optional[bool]
    detail: str


def _text_has_keyword(text: str, keywords: list[str]) -> bool:
    """Whole-word (phrase) match so 'it' does not match 'literature', etc."""
    text = text.lower()
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw.lower())}\b", text):
            return True
    return False


def evaluate_subject(course: Course, degree_subject: Optional[str], degree_title: Optional[str], modules: Optional[list[str]] = None) -> SubjectEvaluation:
    rule = course.subject_rule
    subject_text = " ".join(filter(None, [degree_subject, degree_title]))
    module_text = " ".join(modules or [])
    combined = f"{subject_text} {module_text}".strip()

    if not combined:
        return SubjectEvaluation(None, "No degree subject/title provided to assess relevance.")

    if rule.any_discipline:
        # Data Science: any discipline is fine, but must show maths aptitude.
        if rule.requires_maths_aptitude:
            if _text_has_keyword(combined, MATHS_KEYWORDS):
                return SubjectEvaluation(True, f"Any discipline accepted; mathematical aptitude evidenced in '{combined[:80]}'.")
            return SubjectEvaluation(
                None,
                "Any discipline is accepted, but mathematical aptitude (e.g. A-level/BTEC Maths or quantitative "
                "modules) was not clearly evidenced — flag for review.",
            )
        return SubjectEvaluation(True, "Any discipline is accepted for this course.")

    # Specific subject courses (AI, Software Engineering)
    subject_ok = _text_has_keyword(subject_text, rule.acceptable_keywords) or _text_has_keyword(module_text, rule.acceptable_keywords)
    prog_ok = True
    if rule.requires_programming:
        prog_ok = _text_has_keyword(combined, PROGRAMMING_KEYWORDS)

    if subject_ok and prog_ok:
        return SubjectEvaluation(True, "Degree subject is a relevant CS/STEM discipline with programming content.")
    if subject_ok and not prog_ok:
        return SubjectEvaluation(None, "Subject is STEM but programming content was not clearly evidenced — flag for review.")
    return SubjectEvaluation(False, f"Degree subject '{subject_text or combined[:80]}' does not appear to be a relevant CS/STEM discipline.")
