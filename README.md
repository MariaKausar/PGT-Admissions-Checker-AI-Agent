# Salford PGT Admissions Agent

An agentic system that assesses whether applications for **Taught Masters courses at the University of
Salford** satisfy entrance requirements. Built for the Grow AI Team demonstration to the SME.

It reads an applicant's documents (course-choice sheet, degree certificate, transcript) as **PDF or JPG**,
extracts the key facts with **Claude (via LangChain)**, and runs a deterministic, auditable rules engine to
return an **ACCEPT / REJECT / REVIEW** decision with a full breakdown of every check.

Supported courses (criteria verified against the Salford course pages):

| Course | Code | Degree requirement | English |
| --- | --- | --- | --- |
| MSc Artificial Intelligence | i403T* | 2:2 in CS / related STEM **with programming content** | IELTS 6.0, no band < 5.5 |
| MSc Data Science | i402T* | 2:2 in **any discipline** **with mathematical aptitude** | IELTS 6.0, no band < 5.5 |
| MSc Software Engineering | i404T* | 2:2 in CS / related STEM **with computer programming** | IELTS 6.0, no band < 5.5 |

\* **Admission codes:** `i403T` is from the candidate brief example. Salford PGT applications are submitted via the university portal (not UCAS); `i402T` / `i404T` follow the same illustrative format for this demo. Confirm exact codes with the admissions team before production.

## Key capabilities

- **Dynamic intake dates** — never hardcoded. Open intakes (January / September) are generated relative to
  today's date, `INTAKE_YEARS_AHEAD` years forward.
- **International grade conversion** — India, Pakistan, Bangladesh, Nigeria, China + a generic fallback, each
  mapped to the UK **2:2** bar (percentage or CGPA). Borderline grades are flagged for human review.
- **English-language logic** — applicants from majority English-speaking countries (or whose first language is
  English) are exempt; otherwise **IELTS ≥ 6.0 overall with no band below 5.5** is enforced.
- **Per-course subject rules** — AI & Software Engineering require a relevant CS/STEM degree with programming;
  Data Science accepts any discipline but requires demonstrable mathematical aptitude.
- **LangChain tool-calling agent** — admissions staff can chat with the agent to ask ad-hoc questions
  ("does 58% from India meet the 2:2?", "is September 2027 a valid intake?").

## Architecture

```
Frontend (React + Vite)  ──►  Backend (FastAPI)
                                 ├─ /api/extract   Claude multimodal doc reading (LangChain)
                                 ├─ /api/assess    extract + deterministic rules engine
                                 ├─ /api/assess-json  rules engine on structured data (no LLM)
                                 ├─ /api/chat      LangChain tool-calling agent
                                 └─ /api/courses   course + dynamic intake info
```

- **Document reading** uses Claude's vision through LangChain (`ChatAnthropic.with_structured_output`).
- **Decisions** are made by a deterministic engine (`app/services/assessment.py`) so they are repeatable and
  auditable — the LLM extracts and explains, the rules decide.

## Prerequisites

- **Python 3.12** (Python 3.14 currently has no `pydantic-core` wheel). This repo was set up with
  [`uv`](https://docs.astral.sh/uv/), which installs Python 3.12 automatically.
- **Node.js 18+** and npm.
- An **Anthropic API key**.

## Backend setup

```bash
cd backend

# create the environment (uv installs Python 3.12 if needed)
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt

# configure your key
copy .env.example .env      # macOS/Linux: cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY (and ANTHROPIC_MODEL if desired)

# run the API
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Offline demo (no API key needed)

```bash
.venv\Scripts\python.exe demo.py              # guided 20-min presentation script
.venv\Scripts\python.exe demo_samples.py      # quick sample decisions
.venv\Scripts\python.exe verify_grades.py     # 17 country/grade test cases
```

### Sample documents for live upload demo

```bash
.venv\Scripts\python.exe generate_samples.py
```

Creates three applicant folders under `backend/sample_documents/`:

| Folder | Country | Course | Expected |
| --- | --- | --- | --- |
| `applicant_1/` | India | MSc AI | **ACCEPT** |
| `applicant_2/` | Pakistan | MSc Software Engineering | **REJECT** (IELTS writing 5.0) |
| `applicant_3/` | Bangladesh | MSc Data Science | **ACCEPT** |

Upload all PDFs from one folder in the **Case assessment** tab.

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The dev server proxies `/api` to the backend on port 8000.

## Configuration (`backend/.env`)

| Variable | Default | Purpose |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | — | Your Claude API key |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Model snapshot (change to one your account can access) |
| `AGENT_TEMPERATURE` | `0` | Keep low for deterministic behaviour |
| `INTAKE_YEARS_AHEAD` | `2` | How many years of future intakes are considered "open" |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS origin |

## Where the rules live (for admissions staff to tune)

- `backend/app/services/criteria.py` — course definitions, subject rules, IELTS thresholds, dynamic intakes.
- `backend/app/services/country_rules.py` — English-speaking countries + grade-to-2:2 conversion tables.

> The international grade thresholds are typical UK ENIC/NARIC-style mappings and should be signed off by the
> admissions team before production use.

## Next steps

- Add remaining PGT courses and per-course document checklists.
- Replace the in-memory chat session store with Redis/DB.
- Persist assessments and add an audit log / caseworker queue.
- Human-in-the-loop UI for REVIEW cases; confidence-based auto-routing.
- Fraud/authenticity checks on certificates; ENIC integration for grade equivalence.
```
