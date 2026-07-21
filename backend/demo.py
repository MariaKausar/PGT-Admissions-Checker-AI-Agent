"""Guided 20-minute demonstration script (pure Python, run in the terminal).

Maps directly to the interview brief's required flow:
    1. Summary of options explored
    2. Sample code (the design)
    3. Key capabilities illustrated with samples
    4. Next steps

Run:
    .venv\\Scripts\\python.exe demo.py            # run the whole talk
    .venv\\Scripts\\python.exe demo.py --pause     # pause between sections (press Enter)

No API key or LLM is required: this uses the deterministic rules engine so the
demo is fast, offline and repeatable. The LLM document-reading step is described
(and can be shown live in the browser via /api/assess).
"""
from __future__ import annotations

import sys
from datetime import date

from app.models.schemas import ExtractedApplication, IeltsScores, TranscriptModule
from app.services import country_rules as cr
from app.services import criteria as crit
from app.services.assessment import assess_application

PAUSE = "--pause" in sys.argv

# --------------------------------------------------------------------------------------
# Small presentation helpers
# --------------------------------------------------------------------------------------
LINE = "=" * 82


def header(title: str) -> None:
    print("\n" + LINE)
    print(f"  {title}")
    print(LINE)


def sub(title: str) -> None:
    print(f"\n--- {title} ---")


def gate() -> None:
    if PAUSE:
        try:
            input("\n[Enter] to continue...")
        except (EOFError, KeyboardInterrupt):
            pass


def verdict(passed) -> str:
    return "PASS" if passed is True else "FAIL" if passed is False else "REVIEW"


def show_assessment(sample: ExtractedApplication) -> None:
    result = assess_application(sample)
    print(f"\n  Applicant : {sample.applicant_name}  ({sample.awarding_country})")
    print(f"  Applied to: {sample.course_name}  [{sample.month_of_entry} {sample.year_of_entry}]")
    print(f"  DECISION  : {result.decision.value}   (confidence: {result.confidence})")
    print(f"  Summary   : {result.summary}")
    for c in result.checks:
        print(f"     [{verdict(c.passed):>6}] {c.name}: {c.detail}")


# --------------------------------------------------------------------------------------
# SECTION 1 - Options explored
# --------------------------------------------------------------------------------------
def section_options() -> None:
    header("1. OPTIONS EXPLORED")
    print(
        """
  Problem: manually checking whether PGT applicants meet entrance requirements is
  slow and inconsistent. We assessed three design options.

  Option A - Pure LLM ("read the docs and just decide")
     + Fast to prototype, flexible with messy documents.
     - Decisions are not repeatable or auditable; can hallucinate thresholds;
       hard for admissions staff to trust or defend a REJECT.

  Option B - Pure rules engine (hard-coded checks, manual data entry)
     + Fully deterministic and auditable.
     - Someone still has to read every PDF/JPG by hand -> no time saved.

  Option C (CHOSEN) - Agentic hybrid:
     * LLM (Claude via LangChain) READS the PDF/JPG documents and EXTRACTS
       structured facts (course, grade, country, IELTS, modules).
     * A deterministic rules engine DECIDES ACCEPT / REJECT / REVIEW.
     * A LangChain tool-calling agent answers ad-hoc admissions questions.
     => The LLM does what it is good at (reading), rules do what they are good
        at (consistent, explainable decisions). Every decision cites its rule.
"""
    )
    gate()


# --------------------------------------------------------------------------------------
# SECTION 2 - Sample code / design
# --------------------------------------------------------------------------------------
def section_design() -> None:
    header("2. THE DESIGN (sample code walkthrough)")
    print(
        """
  Pipeline:
      Upload PDF/JPG  ->  Claude extraction (LangChain)  ->  ExtractedApplication
                      ->  deterministic rules engine     ->  AssessmentResult

  Key modules:
      app/services/document_parser.py  - Claude multimodal reading -> structured data
      app/services/criteria.py         - course rules, IELTS, DYNAMIC intake dates
      app/services/country_rules.py    - English-speaking exemption + grade conversion
      app/services/assessment.py       - combines checks into ACCEPT/REJECT/REVIEW
      app/agent/                       - LangChain tool-calling agent for Q&A
      app/main.py                      - FastAPI endpoints (/assess, /chat, ...)
"""
    )

    sub("Verified Salford entry criteria (the three courses)")
    for c in crit.COURSES.values():
        print(f"   * {c.name} [{c.admission_code}] - min {c.min_uk_classification}")
        print(f"       {c.subject_rule.description}")
    print("   * English (all): IELTS 6.0 overall, no band < 5.5 (waived if exempt).")

    sub("DYNAMIC intake dates - generated from today's date, never hard-coded")
    print(f"   Today is {date.today().isoformat()}. Currently open intakes:")
    for o in crit.valid_intakes():
        print(f"       - {o['month']} {o['year']}")
    gate()


# --------------------------------------------------------------------------------------
# SECTION 3 - Key capabilities illustrated with samples
# --------------------------------------------------------------------------------------
def section_capabilities() -> None:
    header("3. KEY CAPABILITIES (illustrated with samples)")

    sub("Capability A - International grade conversion to the UK 2:2 bar")
    for country, pct, cgpa, scale in [
        ("India", 68.0, None, None),
        ("India", 48.0, None, None),
        ("Pakistan", None, 3.1, 4.0),
        ("Bangladesh", None, 2.3, 4.0),
    ]:
        ev = cr.evaluate_degree_grade(country=country, percentage=pct, cgpa=cgpa, cgpa_scale=scale)
        given = f"{pct}%" if pct is not None else f"CGPA {cgpa}/{scale:.0f}"
        print(f"   {country:<11} {given:<12} -> meets 2:2? {str(ev.meets_2_2):<5}  ({ev.detail})")
    gate()

    sub("Capability B - English-language logic (country exemption vs IELTS)")
    for country, fle, ielts in [
        ("United Kingdom", None, None),
        ("Nigeria", None, None),  # majority English-speaking -> exempt
        ("India", None, IeltsScores(overall=6.0, listening=6.0, reading=6.0, writing=5.0, speaking=6.0)),
        ("India", None, IeltsScores(overall=6.5, listening=6.5, reading=6.0, writing=6.0, speaking=6.5)),
    ]:
        exempt = cr.is_majority_english_speaking(country)
        if exempt:
            print(f"   {country:<15} -> EXEMPT (majority English-speaking country)")
        else:
            ev = crit.evaluate_ielts(ielts)
            print(f"   {country:<15} -> IELTS required. pass={ev.passed}  ({ev.detail})")
    gate()

    sub("Capability C - End-to-end decisions across realistic applicants")
    print("  (These are the structured facts the LLM would extract from the uploaded docs.)")
    for sample in DEMO_APPLICANTS:
        show_assessment(sample)
    gate()


# --------------------------------------------------------------------------------------
# SECTION 4 - Next steps
# --------------------------------------------------------------------------------------
def section_next_steps() -> None:
    header("4. NEXT STEPS")
    print(
        """
  * Extend to the full Salford PGT catalogue (data-driven course rules already
    make this a config change, not a code change).
  * Human-in-the-loop queue for REVIEW cases; confidence-based auto-routing.
  * ENIC/NARIC integration for authoritative grade equivalence per country.
  * Certificate authenticity / fraud checks.
  * Persist assessments + full audit log (who/what/when/which rule).
  * Batch mode for processing a whole intake; analytics dashboard.
  * Sign-off of grade thresholds with the admissions team before production.

  Live app for the interactive part of the demo:
     backend : .venv\\Scripts\\python.exe -m uvicorn app.main:app --reload --port 8000
     frontend: npm run dev   (http://localhost:5173)  -> upload real PDF/JPG docs
"""
    )


# --------------------------------------------------------------------------------------
# Demo applicants (structured facts as if extracted by the LLM from the documents)
# --------------------------------------------------------------------------------------
DEMO_APPLICANTS: list[ExtractedApplication] = [
    ExtractedApplication(
        applicant_name="Applicant 1", course_name="Artificial Intelligence", admission_code="i403T",
        year_of_entry=2026, month_of_entry="September",
        degree_title="B.Tech Computer Science and Engineering", degree_subject="Computer Science",
        awarding_country="India", percentage=68.0,
        ielts=IeltsScores(overall=6.5, listening=6.5, reading=6.0, writing=6.0, speaking=6.5),
        modules=[TranscriptModule(name="Programming in Python", grade="A"),
                 TranscriptModule(name="Machine Learning", grade="A")],
    ),
    ExtractedApplication(
        applicant_name="Applicant 2", course_name="Software Engineering", admission_code="i404T",
        year_of_entry=2026, month_of_entry="September",
        degree_title="BS Software Engineering", degree_subject="Software Engineering",
        awarding_country="Pakistan", cgpa=3.1, cgpa_scale=4.0,
        ielts=IeltsScores(overall=6.0, listening=6.0, reading=6.0, writing=5.0, speaking=6.0),
    ),
    ExtractedApplication(
        applicant_name="Applicant 3", course_name="Data Science", admission_code="i402T",
        year_of_entry=2027, month_of_entry="January",
        degree_title="BSc Economics", degree_subject="Economics",
        awarding_country="Bangladesh", cgpa=3.4, cgpa_scale=4.0,
        modules=[TranscriptModule(name="Statistics", grade="A"),
                 TranscriptModule(name="Econometrics", grade="A-")],
        ielts=IeltsScores(overall=6.5, listening=6.5, reading=6.5, writing=6.0, speaking=6.0),
    ),
    ExtractedApplication(
        applicant_name="Sara Ali", course_name="Artificial Intelligence", admission_code="i403T",
        year_of_entry=2026, month_of_entry="September",
        degree_title="BA English Literature", degree_subject="English Literature",
        awarding_country="India", percentage=70.0,
        ielts=IeltsScores(overall=7.0, listening=7.0, reading=7.0, writing=6.5, speaking=7.0),
    ),
    ExtractedApplication(
        applicant_name="Wei Chen", course_name="Data Science", admission_code="i402T",
        year_of_entry=2026, month_of_entry="September",
        degree_title="BEng Mathematics and Computing", degree_subject="Mathematics",
        awarding_country="China", percentage=78.0,
    ),
]


def main() -> None:
    header("SALFORD PGT ADMISSIONS AGENT - SME DEMONSTRATION")
    print("  Presenter demo. Flow: options -> design -> capabilities -> next steps.")
    if not PAUSE:
        print("  Tip: run with '--pause' to step through section by section.")
    gate()
    section_options()
    section_design()
    section_capabilities()
    section_next_steps()
    header("END OF DEMONSTRATION - questions welcome")


if __name__ == "__main__":
    main()
