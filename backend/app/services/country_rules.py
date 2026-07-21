"""Country-based rules: English-language exemption and international grade conversion.

Evaluation order (always):
  1. Identify awarding country of the degree
  2. Load that country's grading system (percentage and/or CGPA scale)
  3. Read the applicant's achieved marks (percentage or CGPA + scale from documents)
  4. Compare achievement against the UK 2:2 equivalent for that country
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# --------------------------------------------------------------------------------------
# English-speaking countries (IELTS exemption)
# --------------------------------------------------------------------------------------
MAJORITY_ENGLISH_SPEAKING_COUNTRIES = {
    "antigua and barbuda", "australia", "the bahamas", "bahamas", "barbados", "belize",
    "canada", "dominica", "grenada", "guyana", "ireland", "jamaica", "malta",
    "new zealand", "st kitts and nevis", "saint kitts and nevis", "st lucia",
    "saint lucia", "st vincent and the grenadines", "saint vincent and the grenadines",
    "trinidad and tobago", "united kingdom", "uk", "united states",
    "united states of america", "usa", "us",
}


def is_majority_english_speaking(country: Optional[str]) -> bool:
    if not country:
        return False
    return country.strip().lower() in MAJORITY_ENGLISH_SPEAKING_COUNTRIES


# --------------------------------------------------------------------------------------
# Per-country grading profiles
# --------------------------------------------------------------------------------------
@dataclass
class CountryGradingProfile:
    """How degrees from this country are graded and what maps to a UK 2:2."""

    country: str
    # Percentage-based grading (e.g. India, Pakistan, China)
    uses_percentage: bool = True
    min_percentage_2_2: Optional[float] = None
    # CGPA-based grading
    uses_cgpa: bool = False
    cgpa_scale: Optional[float] = None       # native scale (e.g. 4, 5, 10)
    min_cgpa_2_2: Optional[float] = None     # minimum CGPA on that scale for UK 2:2
    borderline_margin_pct: float = 3.0
    notes: str = ""


COUNTRY_PROFILES: dict[str, CountryGradingProfile] = {
    "india": CountryGradingProfile(
        country="India",
        uses_percentage=True,
        min_percentage_2_2=55.0,
        uses_cgpa=True,
        cgpa_scale=10.0,
        min_cgpa_2_2=6.0,
        notes="India: 55% or CGPA 6.0/10 ≈ UK 2:2. Some transcripts also show GPA/4.",
    ),
    "pakistan": CountryGradingProfile(
        country="Pakistan",
        uses_percentage=True,
        min_percentage_2_2=55.0,
        uses_cgpa=True,
        cgpa_scale=4.0,
        min_cgpa_2_2=2.5,
        notes="Pakistan: 55% or CGPA 2.5/4 ≈ UK 2:2.",
    ),
    "bangladesh": CountryGradingProfile(
        country="Bangladesh",
        uses_percentage=True,
        min_percentage_2_2=55.0,
        uses_cgpa=True,
        cgpa_scale=4.0,
        min_cgpa_2_2=2.5,
        notes="Bangladesh: 55% or CGPA 2.5/4 ≈ UK 2:2.",
    ),
    "nigeria": CountryGradingProfile(
        country="Nigeria",
        uses_percentage=False,
        uses_cgpa=True,
        cgpa_scale=5.0,
        min_cgpa_2_2=2.2,
        notes="Nigeria: CGPA 2.2/5 (Second Class Lower) ≈ UK 2:2.",
    ),
    "china": CountryGradingProfile(
        country="China",
        uses_percentage=True,
        min_percentage_2_2=70.0,
        uses_cgpa=False,
        notes="China: ~70% ≈ UK 2:2 depending on institution tier.",
    ),
}

DEFAULT_PROFILE = CountryGradingProfile(
    country="Unknown",
    uses_percentage=True,
    min_percentage_2_2=55.0,
    uses_cgpa=True,
    cgpa_scale=4.0,
    min_cgpa_2_2=2.5,
    notes="No country-specific profile; using generic 55% or CGPA 2.5/4. Refer to ENIC.",
)

# Fallback 2:2 thresholds when the document states a scale different from the country default.
SCALE_2_2_THRESHOLDS: dict[float, float] = {
    4.0: 2.5,
    5.0: 2.2,
    10.0: 6.0,
}


def get_country_profile(country: Optional[str]) -> CountryGradingProfile:
    if country and country.strip().lower() in COUNTRY_PROFILES:
        return COUNTRY_PROFILES[country.strip().lower()]
    if country:
        return CountryGradingProfile(
            country=country.strip().title(),
            uses_percentage=True,
            min_percentage_2_2=55.0,
            uses_cgpa=True,
            cgpa_scale=4.0,
            min_cgpa_2_2=2.5,
            notes=f"No dedicated profile for {country}; using generic thresholds. Refer to ENIC.",
        )
    return DEFAULT_PROFILE


# Keep backward-compatible alias used elsewhere.
def get_grade_rule(country: Optional[str]) -> CountryGradingProfile:
    p = get_country_profile(country)
    return p


@dataclass
class GradeEvaluation:
    meets_2_2: Optional[bool]
    borderline: bool
    detail: str


def _uk_classification_check(uk_classification: str) -> Optional[GradeEvaluation]:
    cls = uk_classification.replace(" ", "").lower()
    if any(tok in cls for tok in ["first", "1st", "2:1", "2.1", "2:2", "2.2", "upper", "lower"]):
        return GradeEvaluation(
            True, False,
            f"Stated UK classification '{uk_classification}' meets the 2:2 minimum.",
        )
    if any(tok in cls for tok in ["third", "3rd", "3:0", "pass"]):
        return GradeEvaluation(
            False, False,
            f"Stated UK classification '{uk_classification}' is below a 2:2.",
        )
    return None


def _resolve_cgpa_scale(
    profile: CountryGradingProfile,
    cgpa: float,
    cgpa_scale: Optional[float],
) -> tuple[float, float, str]:
    """Step 2b: decide which CGPA scale and 2:2 bar apply.

    Priority:
      1. Scale stated on the document (most reliable)
      2. Country's native CGPA scale (if the value fits it)
      3. Magnitude inference only when country scale does not fit
    """
    if cgpa_scale:
        scale = cgpa_scale
        source = "stated on document"
    elif cgpa <= 4.0:
        # Values ≤ 4.0 are always on a /4 scale — no country awards a degree with 2.83/10.
        scale = 4.0
        source = "inferred /4 scale (CGPA ≤ 4.0)"
    elif profile.uses_cgpa and profile.cgpa_scale and cgpa <= profile.cgpa_scale:
        scale = profile.cgpa_scale
        source = f"{profile.country} standard scale"
    elif cgpa <= 5.0:
        scale = 5.0
        source = "inferred /5 scale from CGPA value"
    else:
        scale = 10.0
        source = "inferred /10 scale from CGPA value"

    # Use country threshold when scale matches the country's native system.
    if profile.uses_cgpa and profile.cgpa_scale == scale and profile.min_cgpa_2_2 is not None:
        threshold = profile.min_cgpa_2_2
    else:
        threshold = SCALE_2_2_THRESHOLDS.get(scale, 2.5 * (scale / 4.0))

    return scale, threshold, source


def _compare_percentage(achieved: float, minimum: float, country: str, margin: float) -> GradeEvaluation:
    if achieved >= minimum:
        verdict = "PASS (meets 2:2)."
    elif achieved >= minimum - margin:
        return GradeEvaluation(
            False, True,
            f"Step 4 — Compare: {achieved:.1f}% vs {minimum:.0f}% required ({country} 2:2 bar). "
            f"Just below threshold (borderline).",
        )
    else:
        verdict = "FAIL (below 2:2)."
    return GradeEvaluation(
        achieved >= minimum,
        False,
        f"Step 4 — Compare: {achieved:.1f}% vs {minimum:.0f}% required ({country} 2:2 bar). {verdict}",
    )


def _compare_cgpa(
    achieved: float,
    scale: float,
    threshold: float,
    country: str,
    scale_source: str,
) -> GradeEvaluation:
    scale_txt = f"/{scale:g}"
    header = (
        f"Step 2 — Grading system: CGPA {scale_txt} ({scale_source}); "
        f"UK 2:2 equivalent for {country} = {threshold:g}{scale_txt}. "
        f"Step 3 — Applicant achieved: CGPA {achieved:g}{scale_txt}. "
    )
    if achieved >= threshold:
        return GradeEvaluation(True, False, header + "Step 4 — Compare: PASS (meets 2:2).")
    if achieved >= threshold * 0.95:
        return GradeEvaluation(
            False, True,
            header + f"Step 4 — Compare: Just below {threshold:g}{scale_txt} (borderline).",
        )
    return GradeEvaluation(
        False, False,
        header + f"Step 4 — Compare: FAIL (below {threshold:g}{scale_txt}).",
    )


def evaluate_degree_grade(
    country: Optional[str],
    percentage: Optional[float] = None,
    cgpa: Optional[float] = None,
    cgpa_scale: Optional[float] = None,
    uk_classification: Optional[str] = None,
) -> GradeEvaluation:
    """Country-first grade evaluation against the UK 2:2 minimum."""

    # UK classification on certificate — direct check, no conversion needed.
    if uk_classification:
        direct = _uk_classification_check(uk_classification)
        if direct:
            return direct

    # Step 1 — Country must be known before any conversion.
    if not country or not country.strip():
        return GradeEvaluation(
            None, False,
            "Step 1 — Awarding country: not provided. Cannot apply country-specific grade rules. "
            "Please confirm the country where the degree was awarded.",
        )

    profile = get_country_profile(country)
    step1 = f"Step 1 — Awarding country: {profile.country}."

    # Step 2 + 3 + 4 — Percentage path (preferred when country uses percentage grading).
    if percentage is not None and profile.uses_percentage and profile.min_percentage_2_2 is not None:
        step2 = (
            f"Step 2 — Grading system: percentage marks ({profile.country} standard; "
            f"UK 2:2 ≈ {profile.min_percentage_2_2:.0f}%). "
            f"Step 3 — Applicant achieved: {percentage:.1f}%."
        )
        result = _compare_percentage(
            percentage, profile.min_percentage_2_2, profile.country, profile.borderline_margin_pct,
        )
        return GradeEvaluation(
            result.meets_2_2, result.borderline, f"{step1} {step2} {result.detail}",
        )

    # Step 2 + 3 + 4 — CGPA path.
    if cgpa is not None:
        scale, threshold, scale_source = _resolve_cgpa_scale(profile, cgpa, cgpa_scale)
        result = _compare_cgpa(cgpa, scale, threshold, profile.country, scale_source)
        return GradeEvaluation(result.meets_2_2, result.borderline, f"{step1} {result.detail}")

    # Nothing to compare.
    systems = []
    if profile.uses_percentage and profile.min_percentage_2_2:
        systems.append(f"percentage (min {profile.min_percentage_2_2:.0f}%)")
    if profile.uses_cgpa and profile.min_cgpa_2_2 and profile.cgpa_scale:
        systems.append(f"CGPA (min {profile.min_cgpa_2_2:g}/{profile.cgpa_scale:g})")
    systems_txt = " or ".join(systems) if systems else "percentage or CGPA"
    return GradeEvaluation(
        None, False,
        f"{step1} Step 2 — Grading system for {profile.country}: {systems_txt}. "
        f"Step 3 — No marks/CGPA found on the documents. Cannot compare.",
    )
