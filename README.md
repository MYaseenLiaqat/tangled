# Tangled

An AI course assistant that tells instructors **which topics their class is genuinely confused about**, without asking students one by one.
Students ask questions inside their course materials; Tangled answers from those materials (RAG) and, in the background, analyses each
question. The instructor sees a short list of topics that need attention, with the evidence behind each.

## Stack and why

| Layer | Choice | Why |
|---|---|---|
| API | **FastAPI** (Python 3.12) | async I/O for bursty LLM calls (a whole class pressing Enter at once), typed schemas, free OpenAPI docs at `/docs` (this is the future integration API), and the Python ML stack in the same process |
| DB | SQLModel + SQLite (Postgres by changing `DATABASE_URL`) | zero setup for the pilot, same code later |
| Vector search | ChromaDB (local, cosine) with the built-in ONNX MiniLM embeddings | free, no GPU or torch, no rate limits |
| LLM | any OpenAI-compatible API (`LLM_BASE_URL`, `LLM_MODEL`) | switch provider without code changes |
| Frontend | React 18 + Vite + TypeScript | separate student and instructor apps in one codebase |

Django was considered. It would add an admin and auth you do not need here, while this project's weight is async LLM calls and ML,
where FastAPI is the lighter and more natural fit.

## How confusion is detected (the core of the project)

```
student message ──► retrieve top passages (Chroma) ──► grounded answer + citations   (student waits only for this)
        │                    │
        │                    └─► topic = the course concept of the retrieved passages (not the chat)
        └─► background: intent classifier ──► confusion | information | other
                         (rubric LLM judge, or trained logistic regression on embeddings)

insights: count DISTINCT students with confusion on a topic
          flag only if  students >= MIN_STUDENTS  AND  a second signal agrees (quiz below QUIZ_LOW, or repeated confusion)
          group the confusion questions by meaning (agglomerative clustering) and highlight the evidence phrase
```

Design choices that control false alarms: per-message (not per-chat) topics, curiosity is classified out, students are counted
once, a minimum student count, required corroboration, a teacher "Not a real problem" button, and low retrieval similarity is treated
as a possible **material gap**, never as confusion. The rules live in `app/services/insights.py` as pure, tested functions.

## Run it

```bash
# backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set LLM_API_KEY and TEACHER_TOKEN
python seed.py                # concepts + 24 student codes (printed once)
uvicorn app.main:app --reload # API docs: http://localhost:8000/docs

# frontend (new terminal)
cd frontend && npm install && npm run dev   # http://localhost:5173
```

Instructor: open the app, enter `TEACHER_TOKEN`, upload materials, then import quiz results (CSV: `item,concept,student_code,answer,correct`).
Students: enter their code. Tests: `cd backend && pytest`.

## Evidence that it works (what you present)

1. `python -m ml.export_labels data/to_label.csv` after the pilot (or after classmates test it) and hand-label ~200 messages; have a second person label too and report Cohen's kappa.
2. `python -m ml.evaluate data/gold.csv` compares the "any follow-up" baseline with embeddings + logistic regression (precision, recall, F1, confusion matrix) and picks a threshold for 85% precision. Set `INTENT_BACKEND=logreg` to use it.
3. Compare topic-level confusion with quiz results, and report how often the instructor pressed "Not a real problem".

## Status: what is tested and what is not

Tested here: decision rules, chunking, auth, and the full pipeline logic end to end with **faked** retrieval, LLM and embeddings (`pytest`, 9 tests);
the frontend type-checks and builds. **Not tested here:** real file ingestion (PDF/PPTX/DOCX), real embeddings and ChromaDB, real LLM calls,
and the clustering on real data. Run the first real upload and chat before relying on any number.

## Known gaps and next steps

- Auth is pilot-grade: a shared teacher token and student codes. Add real auth before any wider use.
- Ingestion is synchronous; move to a job queue for large files. Only PDF previews render in the student app.
- Cluster titles are the first message of each group; an LLM-written title would read better.
- Embeddable widget, LTI 1.3 and an API key scheme (the "Integrations" page is a placeholder).
- Privacy: students are pseudonymous codes, but their questions go to the LLM provider. Tell students, and get the instructor's agreement.
