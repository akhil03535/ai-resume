# ResumeAI — AI Resume Analyzer & Generator

An AI-powered resume analysis and generation platform: upload a resume, match it
against a target job description, verify any skill gaps with the candidate
before they ever touch the output, and generate a tailored, ATS-friendly
resume — with transparent, explainable scoring at every step.

## Product overview

The core journey:

```
Register → Upload Resume → Parse → Review Profile → Add Job Description
→ Analyze (ATS + Job Match scores) → Review missing skills → Verify skills
→ Generate tailored resume → Edit (live preview + AI bullet improvement)
→ Re-analyze → Save version → Download PDF / DOCX
```

### The one rule everything else follows

> AI may optimize, rewrite, reorganize, and tailor information, but it must
> **never fabricate** candidate information — no invented skills, employers,
> metrics, or experience.

Concretely:
- Every skill extracted from a resume starts as `EXTRACTED` — never
  auto-verified.
- Skills the job description needs but the candidate's resume doesn't show
  trigger an interactive **"Do you know Kafka?"** prompt (see
  `app/skills/service.py` and `SkillVerificationModal.tsx`).
- A `no` answer **permanently excludes** that skill from every resume
  generated afterward. A `yes` answer requires the candidate to describe
  where/how they used it — that description becomes stored evidence.
- The AI bullet-improvement tool is instructed to preserve factual meaning
  and never invent metrics that weren't already present.
- ATS and Job Match scores are computed by **deterministic Python code**
  (`app/analysis/scoring.py`), not "ask the LLM for a score." The LLM is only
  used for parsing, extraction, phrasing, and summarization — never scoring.

## Architecture

```
frontend/        React 18 + TypeScript + Vite + Tailwind CSS
backend/         FastAPI + SQLAlchemy 2.x + Alembic + PostgreSQL + Redis
docker-compose.yml
```

Backend module layout (`backend/app/`):

```
core/        settings, DB session, Redis, JWT/password security
common/      shared mixins, exceptions, auth dependency
auth/        register/login/refresh
users/       user model
profiles/    candidate profile — the central source of truth
skills/      the missing-skill verification workflow
jobs/        job description storage + AI-driven requirement extraction
resumes/     resume upload, text extraction, AI parsing
analysis/    deterministic matching + scoring engine, recommendations
generator/   tailored resume generation, bullet improvement, versioning
ai/          AIProvider interface + Groq implementation (swappable)
documents/   PDF/DOCX text extraction and PDF/DOCX export
templates/   data-driven resume template registry + shared Jinja2 template
dashboard/   career overview aggregation
```

### Why no autonomous AI agent?

This app deliberately uses a **controlled, deterministic backend workflow**
(upload → parse → analyze → match → ask user → verify → generate → export)
rather than an autonomous LangChain/LangGraph-style agent. The process
requires predictable behavior and an explicit human-in-the-loop verification
step for anything that will end up as a factual claim on someone's resume —
that's a poor fit for an agent that plans its own steps. The `AIProvider`
interface is intentionally the *only* AI seam in the codebase, which is what
will let a future autonomous AI Interviewer or AI Job Agent be added later
without touching this app's core logic — they'd consume the same
`CandidateProfile` and resume infrastructure.

## Tech stack

**Frontend:** React, TypeScript, Vite, Tailwind CSS, React Router, TanStack
Query, React Hook Form, Axios, Recharts, Lucide icons.

**Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic,
PostgreSQL, Redis, JWT auth, Argon2 password hashing.

**AI:** Groq API by default, behind an `AIProvider` abstract interface
(`app/ai/base.py`) so the vendor can be swapped without touching business
logic. Structured outputs are validated with Pydantic — malformed AI output
is rejected and retried, never trusted blindly.

**Documents:** PyMuPDF (PDF text extraction), python-docx (DOCX read/write),
WeasyPrint (HTML/CSS → PDF export pipeline).

**Matching:** deterministic normalized keyword matching + sentence-transformers
semantic similarity (`all-MiniLM-L6-v2`, lazily loaded, with a lexical
fallback if unavailable) — never "ask the LLM to score this."

## Local setup

### Prerequisites
- Docker and Docker Compose
- A [Groq API key](https://console.groq.com) (free tier available)

### Run it

```bash
cp backend/.env.example backend/.env
# edit backend/.env and set GROQ_API_KEY, and a real JWT_SECRET

docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs

The backend container runs `alembic upgrade head` automatically on startup —
you should never need to modify the database by hand.

### Running without Docker

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # point DATABASE_URL / REDIS_URL at local instances
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

## Environment variables

See `backend/.env.example` and `frontend/.env.example`. Never commit a real
`.env` file — only `.env.example` placeholders are checked in.

Key backend variables:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string (AI response caching) |
| `JWT_SECRET` | Secret for signing access/refresh tokens |
| `GROQ_API_KEY` | AI provider API key |
| `AI_MODEL` | Groq model name |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins |
| `MAX_UPLOAD_SIZE_MB` | Resume upload size limit |

## API overview

All routes are prefixed `/api`. Full interactive docs at `/docs` once running.

```
/api/auth           register, login, refresh, me
/api/profile         get/update candidate profile
/api/resumes         upload, list, get, parse
/api/jobs             create, list, get, analyze
/api/skills          missing-skill prompts, verify
/api/analysis        run analysis, get, list-by-job
/api/generator       templates, generate, CRUD on generated resumes,
                     improve-bullet, export/pdf, export/docx
/api/dashboard       career overview aggregation
```

Every response uses Pydantic response models — SQLAlchemy models are never
returned directly.

## Testing

```bash
cd backend
pip install -r requirements.txt
pytest app/tests/ -v
```

Tests use an in-memory SQLite database for speed and cover:
- The deterministic scoring/matching engine (`test_scoring.py`)
- **The critical rule from the spec**: if a user answers "No" to a missing
  skill, that skill must never become eligible for resume generation, and a
  verified "Yes" answer with evidence must be eligible
  (`test_skill_verification.py`).

## Security considerations

- Passwords hashed with Argon2 (`passlib`).
- JWT access + refresh tokens, with automatic refresh handled client-side.
- File uploads validated by extension, MIME type, **and magic bytes** (never
  trust the filename alone), plus a size cap.
- All API responses go through Pydantic schemas — no ORM model leakage.
- CORS restricted to configured origins.
- No secrets in logs; internal errors are logged server-side and returned to
  the client as generic, safe messages.
- `.env` is git-ignored; only `.env.example` is committed.

## Future architecture: AI Interviewer & AI Job Agent

The `CandidateProfile` (with its verified/basic/rejected skill states and
evidence) and the resume generation/versioning infrastructure are designed to
be reused as-is by future products:
- An **AI Interviewer** could pull the same verified skill evidence to ask
  realistic behavioral/technical questions.
- An **AI Job Agent** could consume the same profile + generated resumes to
  autonomously apply to matching roles.

Both would plug into the existing `AIProvider` interface and `CandidateProfile`
schema rather than requiring a data model rework.

## Project structure

```
resumeai/
├── backend/
│   ├── app/                # see module layout above
│   ├── alembic/             # migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/             # typed API client modules
│   │   ├── components/      # reusable UI (Layout, charts, modals, states)
│   │   ├── hooks/           # useAuth
│   │   ├── pages/           # one file per route
│   │   └── types/           # shared TS types mirroring backend schemas
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml
└── README.md
```
