"""LangChain tools exposing the admissions rules to the agent.

These let the agent (and admissions staff via chat) ask questions like
"what are the requirements for Data Science?", "does 58% from India meet the 2:2?",
"is September 2027 a valid intake?", or "does this IELTS profile pass?".
"""
from __future__ import annotations

import json
from typing import Optional

from langchain_core.tools import tool

from app.models.schemas import IeltsScores
from app.services import country_rules as cr
from app.services import criteria as crit


@tool
def list_courses() -> str:
    """List the supported PGT courses and their entrance requirements."""
    out = []
    for c in crit.COURSES.values():
        out.append({
            "course": c.name,
            "admission_code": c.admission_code,
            "min_classification": c.min_uk_classification,
            "requirement": c.subject_rule.description,
            "english": "IELTS 6.0 overall, no band below 5.5 (if English not first language).",
        })
    return json.dumps(out, indent=2)


@tool
def get_course_requirements(course_name: str) -> str:
    """Get the full entrance requirements for a single course by name or admission code."""
    course = crit.find_course(course_name, course_name)
    if not course:
        return f"No supported course matched '{course_name}'. Supported: MSc Artificial Intelligence, MSc Data Science, MSc Software Engineering."
    return json.dumps({
        "course": course.name,
        "admission_code": course.admission_code,
        "min_classification": course.min_uk_classification,
        "requirement": course.subject_rule.description,
        "requires_programming": course.subject_rule.requires_programming,
        "requires_maths_aptitude": course.subject_rule.requires_maths_aptitude,
        "any_discipline": course.subject_rule.any_discipline,
        "english": "IELTS 6.0 overall, no band below 5.5 (if English not first language).",
        "valid_months": list(course.valid_months),
    }, indent=2)


@tool
def check_valid_intake(month: str, year: int) -> str:
    """Check whether a given entry month and year is a currently-open intake (dynamic, based on today's date)."""
    ok, detail = crit.is_valid_intake(month, year)
    options = crit.valid_intakes()
    return json.dumps({
        "valid": ok,
        "detail": detail,
        "open_intakes": [f"{o['month']} {o['year']}" for o in options],
    }, indent=2)


@tool
def convert_grade_to_uk(country: str, percentage: Optional[float] = None, cgpa: Optional[float] = None, cgpa_scale: Optional[float] = None) -> str:
    """Check whether an international grade meets the UK 2:2 minimum.

    Provide the awarding country and EITHER a percentage OR a cgpa (+ optional scale).
    Supports India, Pakistan, Bangladesh, Nigeria, China and a generic fallback.
    """
    ev = cr.evaluate_degree_grade(country=country, percentage=percentage, cgpa=cgpa, cgpa_scale=cgpa_scale)
    profile = cr.get_country_profile(country)
    return json.dumps({
        "country": profile.country,
        "meets_2_2": ev.meets_2_2,
        "borderline": ev.borderline,
        "detail": ev.detail,
        "grading_system": {
            "uses_percentage": profile.uses_percentage,
            "min_percentage_2_2": profile.min_percentage_2_2,
            "uses_cgpa": profile.uses_cgpa,
            "cgpa_scale": profile.cgpa_scale,
            "min_cgpa_2_2": profile.min_cgpa_2_2,
            "notes": profile.notes,
        },
    }, indent=2)


@tool
def check_english_requirement(country: str, first_language_english: Optional[bool] = None,
                              ielts_overall: Optional[float] = None, listening: Optional[float] = None,
                              reading: Optional[float] = None, writing: Optional[float] = None,
                              speaking: Optional[float] = None) -> str:
    """Check the English-language requirement: country exemption first, else IELTS (6.0 overall, no band < 5.5)."""
    if first_language_english is True:
        return json.dumps({"passed": True, "detail": "First language is English — IELTS not required."})
    if cr.is_majority_english_speaking(country):
        return json.dumps({"passed": True, "detail": f"{country} is a majority English-speaking country — IELTS exemption applies."})
    ielts = IeltsScores(overall=ielts_overall, listening=listening, reading=reading, writing=writing, speaking=speaking)
    ev = crit.evaluate_ielts(ielts)
    return json.dumps({"passed": ev.passed, "detail": ev.detail})


AGENT_TOOLS = [
    list_courses,
    get_course_requirements,
    check_valid_intake,
    convert_grade_to_uk,
    check_english_requirement,
]
