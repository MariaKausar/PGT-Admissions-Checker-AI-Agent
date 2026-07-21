"""Offline demo of the assessment engine (no API key / no LLM needed).

Run:  python demo_samples.py
Shows how the deterministic rules decide ACCEPT / REJECT / REVIEW for a range of
realistic international applicants across the three courses.
"""
from __future__ import annotations

from app.models.schemas import DocumentsProvided, ExtractedApplication, IeltsScores, TranscriptModule
from app.services.assessment import assess_application

SAMPLES: list[ExtractedApplication] = [
    # 1) Strong Indian CS applicant for AI -> ACCEPT
    ExtractedApplication(
        applicant_name="Applicant 1",
        course_name="Artificial Intelligence",
        admission_code="i403T",
        year_of_entry=2026,
        month_of_entry="September",
        degree_title="B.Tech Computer Science and Engineering",
        degree_subject="Computer Science",
        awarding_country="India",
        percentage=68.0,
        ielts=IeltsScores(overall=6.5, listening=6.5, reading=6.0, writing=6.0, speaking=6.5),
        modules=[TranscriptModule(name="Programming in Python", grade="A"),
                 TranscriptModule(name="Machine Learning", grade="A")],
        documents_provided=DocumentsProvided(course_choice=True, degree_certificate=True, transcript=True),
    ),
    # 2) Pakistani applicant, IELTS writing below 5.5 -> REJECT
    ExtractedApplication(
        applicant_name="Applicant 2",
        course_name="Software Engineering",
        admission_code="i404T",
        year_of_entry=2026,
        month_of_entry="September",
        degree_title="BS Software Engineering",
        degree_subject="Software Engineering",
        awarding_country="Pakistan",
        cgpa=3.1, cgpa_scale=4.0,
        ielts=IeltsScores(overall=6.0, listening=6.0, reading=6.0, writing=5.0, speaking=6.0),
        modules=[TranscriptModule(name="Software Design", grade="A-")],
        documents_provided=DocumentsProvided(course_choice=True, degree_certificate=True, transcript=True),
    ),
    # 3) Bangladeshi non-CS applicant for Data Science, has maths -> ACCEPT (any discipline + maths)
    ExtractedApplication(
        applicant_name="Applicant 3",
        course_name="Data Science",
        admission_code="i402T",
        year_of_entry=2027,
        month_of_entry="January",
        degree_title="BSc Economics",
        degree_subject="Economics",
        awarding_country="Bangladesh",
        cgpa=3.4, cgpa_scale=4.0,
        modules=[TranscriptModule(name="Statistics", grade="A"),
                 TranscriptModule(name="Econometrics", grade="A-")],
        ielts=IeltsScores(overall=6.5, listening=6.5, reading=6.5, writing=6.0, speaking=6.0),
        documents_provided=DocumentsProvided(course_choice=True, degree_certificate=True, transcript=True),
    ),
    # 4) UK applicant (English exempt), 2:2 -> ACCEPT, no IELTS needed
    ExtractedApplication(
        applicant_name="James Miller",
        course_name="Artificial Intelligence",
        admission_code="i403T",
        year_of_entry=2026,
        month_of_entry="September",
        degree_title="BSc Computer Science",
        degree_subject="Computer Science",
        awarding_country="United Kingdom",
        uk_classification="2:2",
        modules=[TranscriptModule(name="Programming", grade="B")],
        documents_provided=DocumentsProvided(course_choice=True, degree_certificate=True, transcript=True),
    ),
    # 5) Indian applicant below the 2:2 grade bar -> REJECT
    ExtractedApplication(
        applicant_name="Rahul Verma",
        course_name="Software Engineering",
        admission_code="i404T",
        year_of_entry=2026,
        month_of_entry="September",
        degree_title="B.Sc Information Technology",
        degree_subject="Information Technology",
        awarding_country="India",
        percentage=48.0,
        ielts=IeltsScores(overall=6.5, listening=6.5, reading=6.5, writing=6.0, speaking=6.5),
        modules=[TranscriptModule(name="Database Systems", grade="C")],
        documents_provided=DocumentsProvided(course_choice=True, degree_certificate=True, transcript=True),
    ),
    # 6) Non-CS applicant for AI -> REJECT (subject not relevant)
    ExtractedApplication(
        applicant_name="Sara Ali",
        course_name="Artificial Intelligence",
        admission_code="i403T",
        year_of_entry=2026,
        month_of_entry="September",
        degree_title="BA English Literature",
        degree_subject="English Literature",
        awarding_country="India",
        percentage=70.0,
        ielts=IeltsScores(overall=7.0, listening=7.0, reading=7.0, writing=6.5, speaking=7.0),
        modules=[TranscriptModule(name="Poetry", grade="A")],
        documents_provided=DocumentsProvided(course_choice=True, degree_certificate=True, transcript=True),
    ),
    # 7) Missing IELTS entirely, not exempt -> INCOMPLETE (request English evidence)
    ExtractedApplication(
        applicant_name="Wei Chen",
        course_name="Data Science",
        admission_code="i402T",
        year_of_entry=2026,
        month_of_entry="September",
        degree_title="BEng Mathematics and Computing",
        degree_subject="Mathematics",
        awarding_country="China",
        percentage=78.0,
        modules=[TranscriptModule(name="Calculus", grade="A")],
        documents_provided=DocumentsProvided(course_choice=True, degree_certificate=True, transcript=True),
    ),
    # 8) Transcript only uploaded -> INCOMPLETE (per brief)
    ExtractedApplication(
        applicant_name="Unknown Applicant",
        percentage=65.0,
        modules=[TranscriptModule(name="Physics", grade="B+")],
        documents_provided=DocumentsProvided(course_choice=False, degree_certificate=False, transcript=True),
    ),
]


def main() -> None:
    for i, sample in enumerate(SAMPLES, 1):
        result = assess_application(sample)
        print("=" * 78)
        print(f"[{i}] {sample.applicant_name}  ->  {sample.course_name} ({sample.awarding_country})")
        print(f"    DECISION: {result.decision}   (confidence: {result.confidence})")
        print(f"    {result.summary}")
        for c in result.checks:
            mark = "PASS" if c.passed is True else "FAIL" if c.passed is False else "??? "
            print(f"      [{mark}] {c.name}: {c.detail}")
    print("=" * 78)


if __name__ == "__main__":
    main()
