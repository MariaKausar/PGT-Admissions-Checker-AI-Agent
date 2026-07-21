"""Generate realistic sample applicant PDFs for the demo.

Run:  .venv\\Scripts\\python.exe generate_samples.py

Creates sample_documents/ with three complete applicant case files:
  1. applicant_1/   — India, MSc AI, should ACCEPT
  2. applicant_2/   — Pakistan, MSc SWE, IELTS writing fail, should REJECT
  3. applicant_3/   — Bangladesh, MSc Data Science, should ACCEPT
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

OUT = Path(__file__).parent / "sample_documents"


def _pdf(path: Path, draw_fn) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    draw_fn(c, w, h)
    c.save()
    print(f"  created {path.relative_to(OUT.parent)}")


def course_choice(c, w, h, *, name, course, code, year, month):
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, h - 2.5 * cm, "University of Salford — Postgraduate Application")
    c.setFont("Helvetica", 11)
    y = h - 4 * cm
    for label, value in [
        ("Applicant Name", name),
        ("Course", course),
        ("Code", code),
        ("Year of Entry", str(year)),
        ("Month of Entry", month),
    ]:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2 * cm, y, f"{label}:")
        c.setFont("Helvetica", 11)
        c.drawString(7 * cm, y, value)
        y -= 0.9 * cm
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(2 * cm, 2 * cm, "SAMPLE DOCUMENT — for demonstration purposes only")


def degree_certificate(c, w, h, *, name, degree, university, country, grade_line):
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w / 2, h - 3 * cm, university)
    c.setFont("Helvetica", 12)
    c.drawCentredString(w / 2, h - 4 * cm, country)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, h - 6 * cm, "DEGREE CERTIFICATE")
    c.setFont("Helvetica", 11)
    c.drawCentredString(w / 2, h - 7.5 * cm, "This is to certify that")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, h - 8.8 * cm, name)
    c.setFont("Helvetica", 11)
    c.drawCentredString(w / 2, h - 10.2 * cm, f"has been awarded the degree of")
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(w / 2, h - 11.5 * cm, degree)
    c.setFont("Helvetica", 11)
    c.drawCentredString(w / 2, h - 13 * cm, grade_line)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(2 * cm, 2 * cm, "SAMPLE DOCUMENT — for demonstration purposes only")


def transcript(c, w, h, *, name, university, modules, summary_line):
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, h - 2.5 * cm, f"{university} — Academic Transcript")
    c.setFont("Helvetica", 11)
    c.drawString(2 * cm, h - 3.8 * cm, f"Student: {name}")
    y = h - 5.5 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Module")
    c.drawString(12 * cm, y, "Grade")
    y -= 0.5 * cm
    c.line(2 * cm, y, 18 * cm, y)
    y -= 0.6 * cm
    c.setFont("Helvetica", 10)
    for mod, grade in modules:
        c.drawString(2 * cm, y, mod)
        c.drawString(12 * cm, y, grade)
        y -= 0.55 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y - 0.5 * cm, summary_line)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(2 * cm, 2 * cm, "SAMPLE DOCUMENT — for demonstration purposes only")


def build_applicant_1():
    folder = OUT / "applicant_1"
    name = "Applicant 1"
    _pdf(folder / "01_course_choice.pdf", lambda c, w, h: course_choice(
        c, w, h, name=name, course="Artificial Intelligence",
        code="i403T", year=2026, month="September",
    ))
    _pdf(folder / "02_degree_certificate.pdf", lambda c, w, h: degree_certificate(
        c, w, h, name=name,
        degree="Bachelor of Technology in Computer Science and Engineering",
        university="Delhi Technological University", country="India",
        grade_line="Overall Percentage: 68.0%  |  CGPA: 7.2 / 10",
    ))
    _pdf(folder / "03_transcript.pdf", lambda c, w, h: transcript(
        c, w, h, name=name, university="Delhi Technological University",
        modules=[
            ("Programming in Python", "A"),
            ("Data Structures and Algorithms", "A"),
            ("Machine Learning", "A"),
            ("Database Management Systems", "B+"),
            ("Operating Systems", "B+"),
        ],
        summary_line="Overall Percentage: 68.0%  |  CGPA: 7.2 / 10",
    ))
    _pdf(folder / "04_ielts.pdf", lambda c, w, h: (
        c.setFont("Helvetica-Bold", 14),
        c.drawString(2 * cm, h - 3 * cm, "IELTS Academic Test Report Form"),
        c.setFont("Helvetica", 11),
        c.drawString(2 * cm, h - 4.5 * cm, f"Candidate: {name}"),
        c.drawString(2 * cm, h - 5.5 * cm, "Overall Band Score: 6.5"),
        c.drawString(2 * cm, h - 6.8 * cm, "Listening: 6.5   Reading: 6.0   Writing: 6.0   Speaking: 6.5"),
        c.setFont("Helvetica-Oblique", 9),
        c.drawString(2 * cm, 2 * cm, "SAMPLE DOCUMENT — for demonstration purposes only"),
    ))


def build_applicant_2():
    folder = OUT / "applicant_2"
    name = "Applicant 2"
    _pdf(folder / "01_course_choice.pdf", lambda c, w, h: course_choice(
        c, w, h, name=name, course="Software Engineering",
        code="i404T", year=2026, month="September",
    ))
    _pdf(folder / "02_degree_certificate.pdf", lambda c, w, h: degree_certificate(
        c, w, h, name=name,
        degree="Bachelor of Science in Software Engineering",
        university="National University of Computer and Emerging Sciences", country="Pakistan",
        grade_line="CGPA: 3.1 / 4.0",
    ))
    _pdf(folder / "03_transcript.pdf", lambda c, w, h: transcript(
        c, w, h, name=name, university="FAST-NUCES",
        modules=[
            ("Object-Oriented Programming", "A-"),
            ("Software Design and Architecture", "B+"),
            ("Web Technologies", "A"),
            ("Database Systems", "B"),
        ],
        summary_line="CGPA: 3.1 / 4.0",
    ))
    _pdf(folder / "04_ielts.pdf", lambda c, w, h: (
        c.setFont("Helvetica-Bold", 14),
        c.drawString(2 * cm, h - 3 * cm, "IELTS Academic Test Report Form"),
        c.setFont("Helvetica", 11),
        c.drawString(2 * cm, h - 4.5 * cm, f"Candidate: {name}"),
        c.drawString(2 * cm, h - 5.5 * cm, "Overall Band Score: 6.0"),
        c.drawString(2 * cm, h - 6.8 * cm, "Listening: 6.0   Reading: 6.0   Writing: 5.0   Speaking: 6.0"),
        c.setFont("Helvetica-Oblique", 9),
        c.drawString(2 * cm, 2 * cm, "SAMPLE DOCUMENT — for demonstration purposes only"),
    ))


def build_applicant_3():
    folder = OUT / "applicant_3"
    name = "Applicant 3"
    _pdf(folder / "01_course_choice.pdf", lambda c, w, h: course_choice(
        c, w, h, name=name, course="Data Science",
        code="i402T", year=2027, month="January",
    ))
    _pdf(folder / "02_degree_certificate.pdf", lambda c, w, h: degree_certificate(
        c, w, h, name=name,
        degree="Bachelor of Science in Economics",
        university="University of Dhaka", country="Bangladesh",
        grade_line="CGPA: 3.4 / 4.0",
    ))
    _pdf(folder / "03_transcript.pdf", lambda c, w, h: transcript(
        c, w, h, name=name, university="University of Dhaka",
        modules=[
            ("Statistics", "A"),
            ("Econometrics", "A-"),
            ("Mathematics for Economics", "A"),
            ("Microeconomics", "B+"),
        ],
        summary_line="CGPA: 3.4 / 4.0",
    ))
    _pdf(folder / "04_ielts.pdf", lambda c, w, h: (
        c.setFont("Helvetica-Bold", 14),
        c.drawString(2 * cm, h - 3 * cm, "IELTS Academic Test Report Form"),
        c.setFont("Helvetica", 11),
        c.drawString(2 * cm, h - 4.5 * cm, f"Candidate: {name}"),
        c.drawString(2 * cm, h - 5.5 * cm, "Overall Band Score: 6.5"),
        c.drawString(2 * cm, h - 6.8 * cm, "Listening: 6.5   Reading: 6.5   Writing: 6.0   Speaking: 6.0"),
        c.setFont("Helvetica-Oblique", 9),
        c.drawString(2 * cm, 2 * cm, "SAMPLE DOCUMENT — for demonstration purposes only"),
    ))


def main() -> None:
    print("Generating sample applicant documents...")
    build_applicant_1()
    build_applicant_2()
    build_applicant_3()
    print(f"\nDone. Upload folders from:\n  {OUT}")


if __name__ == "__main__":
    main()
