# signal-lite

Interview transcript → themes, each backed by quotes verified to exist in the transcript. Built in 5 stages (script → FastAPI → SQLite → eval → frontend). Full rationale and current stage in @DESIGN.md.

## Stack
Python 3.12, uv, Pydantic v2, FastAPI (Stage 2+), SQLite via stdlib `sqlite3` (Stage 3+), pytest, ruff. Frontend (Stage 5): React + TypeScript via Vite.

## Commands
- `uv run python -m signal_lite.cli transcripts/<file>.txt` — Stage 1 script
- `uv run fastapi dev src/signal_lite/api.py` — API (Stage 2+)
- `uv run pytest` — tests (offline, use FakeLLM)
- `uv run ruff check . && uv run ruff format .`
- `uv run python -m evals.run` — eval scorecard (Stage 4+)

## Working agreement (important)
I'm building this to prepare for a FastAPI/Pydantic interview and have to defend every line.
- **Don't write `analyze()`, the Pydantic models, quote verification, or the prompt unless I explicitly ask.** Default to explaining, reviewing, and asking questions.
- When I propose a design, give the strongest counterargument before agreeing.
- Point me to the relevant FastAPI/Pydantic concept rather than pasting a full solution; short snippets are fine.
- Fine to generate without asking: sample transcripts, test fixtures, FakeLLM canned responses, config/boilerplate.
- Stay in the current stage. Don't pull in later-stage work (DB, frontend) early.
- Never add a dependency without asking. No agent frameworks (D8).
- If a change contradicts a decision in DESIGN.md, flag it; I update the decision log and write the "why".

## Conventions
- `analyze(transcript, llm) -> AnalysisResult` is pure: no file I/O, printing, or HTTP. CLI/API/evals are thin wrappers (D4).
- Raw LLM output → `RawAnalysis` → verify quotes → `AnalysisResult`. Never return unverified quotes (D1, D3).
- Quotes must match a participant turn by `turn_id`. Dropped quotes are counted, not hidden.
- Empty theme list is valid (D2).
- No network calls in tests.
