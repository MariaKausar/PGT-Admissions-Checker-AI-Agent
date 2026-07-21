"""Verify grade evaluation across countries — run before demo.

Run:  .venv\\Scripts\\python.exe verify_grades.py
"""
from __future__ import annotations

from app.services.country_rules import evaluate_degree_grade as e

CASES = [
    # (label, country, pct, cgpa, scale, expected)
    ("India 68% — PASS", "India", 68.0, None, None, True),
    ("India 48% — FAIL", "India", 48.0, None, None, False),
    ("India CGPA 7.2/10 — PASS", "India", None, 7.2, 10.0, True),
    ("India CGPA 5.5/10 — FAIL", "India", None, 5.5, 10.0, False),
    ("India CGPA 2.83/4 — PASS (user case)", "India", None, 2.83, 4.0, True),
    ("India CGPA 2.83 no scale — PASS", "India", None, 2.83, None, True),
    ("Pakistan CGPA 3.1/4 — PASS", "Pakistan", None, 3.1, 4.0, True),
    ("Pakistan CGPA 2.4/4 — borderline FAIL", "Pakistan", None, 2.4, 4.0, False),
    ("Pakistan CGPA 2.83/4 — PASS", "Pakistan", None, 2.83, None, True),
    ("Bangladesh CGPA 3.4/4 — PASS", "Bangladesh", None, 3.4, 4.0, True),
    ("Bangladesh CGPA 2.3/4 — FAIL", "Bangladesh", None, 2.3, 4.0, False),
    ("Nigeria CGPA 2.8/5 — PASS", "Nigeria", None, 2.8, 5.0, True),
    ("Nigeria CGPA 2.0/5 — FAIL", "Nigeria", None, 2.0, 5.0, False),
    ("China 78% — PASS", "China", 78.0, None, None, True),
    ("China 65% — FAIL", "China", 65.0, None, None, False),
    ("No country — cannot check", None, None, 2.83, 4.0, None),
    ("UK 2:2 class — PASS", "United Kingdom", None, None, None, True),
]

def main() -> None:
    print("=" * 80)
    print("GRADE VERIFICATION — country → system → marks → compare")
    print("=" * 80)
    passed = failed = 0
    for label, country, pct, cgpa, scale, expected in CASES:
        uk = "2:2" if label.startswith("UK") else None
        r = e(country=country, percentage=pct, cgpa=cgpa, cgpa_scale=scale, uk_classification=uk)
        ok = r.meets_2_2 == expected
        mark = "OK" if ok else "WRONG"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"\n[{mark}] {label}")
        print(f"      expected={expected}  got={r.meets_2_2}")
        print(f"      {r.detail[:120]}...")
    print("\n" + "=" * 80)
    print(f"Results: {passed} passed, {failed} failed out of {len(CASES)}")
    print("=" * 80)


if __name__ == "__main__":
    main()
