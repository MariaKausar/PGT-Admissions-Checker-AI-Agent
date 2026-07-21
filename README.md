# PGT Admissions Checker

Staff tool for checking Taught Masters applications against University of Salford entrance requirements.

Upload the applicant’s PDFs (or JPGs). The system reads the documents, checks the rules, and suggests **ACCEPT**, **REJECT**, **REVIEW**, or **INCOMPLETE**.

Built as a Grow AI Team demo.

## Courses covered

| Course | Code | Degree background | English |
| --- | --- | --- | --- |
| MSc Artificial Intelligence | i403T | 2:2 in CS / related STEM with programming | IELTS 6.0, no band below 5.5 |
| MSc Data Science | i402T | 2:2 in any subject, with maths aptitude | IELTS 6.0, no band below 5.5 |
| MSc Software Engineering | i404T | 2:2 in CS / related STEM with programming | IELTS 6.0, no band below 5.5 |

Codes are for this demo. Confirm real codes with admissions before live use.

## What it checks

- Required documents (course choice, degree certificate, transcript; IELTS if needed)
- Course match
- Intake month / year
- Degree grade against a UK 2:2 (with country conversion)
- Subject fit for that course
- English language (or exemption)

Document reading uses Claude. The final decision comes from fixed rules in code, so the same case should get the same outcome.

## How to run

You need:

- Python 3.12
- Node.js 18+
- An Anthropic API key

### Backend

```bash
cd backend
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt

copy .env.example .env
# put your ANTHROPIC_API_KEY in .env

.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Sample cases

```bash
cd backend
.venv\Scripts\python.exe generate_samples.py
```

Then upload all PDFs from one folder:

| Folder | Expected |
| --- | --- |
| `applicant_1/` | ACCEPT (MSc AI) |
| `applicant_2/` | REJECT (IELTS writing too low) |
| `applicant_3/` | ACCEPT (MSc Data Science) |

### Offline checks (no API key)

```bash
.venv\Scripts\python.exe demo_samples.py
.venv\Scripts\python.exe verify_grades.py
```

## Settings (`.env`)

| Variable | Default | What it is |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | — | Your API key |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Model name |
| `AGENT_TEMPERATURE` | `0` | Keep low |
| `INTAKE_YEARS_AHEAD` | `2` | How far ahead intakes count as open |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Frontend URL for CORS |

## Where to change the rules

- `backend/app/services/criteria.py` — courses, subject rules, IELTS, intakes
- `backend/app/services/country_rules.py` — country grade conversion and English exemptions

Grade thresholds should be checked with admissions before production.

## Project layout

```
frontend/   React app (upload + results)
backend/    FastAPI API + rules + document reading
```

Main flow: upload → `/api/assess` → read docs → run rules → show result.

## Possible next steps

- More PGT courses
- Save assessment history
- Better handling for REVIEW cases
- Connect to the real applications portal
