# signal-lite — design notes

A small rebuild of the *analysis* half of an AI-facilitated interview platform: read an interview transcript, pull out the themes, and back every theme with quotes that are **proven** to be in the transcript.

> These are starting takes. Argue with every one and rewrite the "why" in your own words — the interview will test whether the opinions are yours.

---

## 1. What the problem actually is

"AI interview analysis" is at least five problems:

| Stage of the real product | Question | Here? |
|---|---|---|
| Design | What are we trying to learn? | Implicit (one prompt) |
| Conduct | How do we get people to say it? (AI interviewer, voice) | **No** — voice is an input adapter; text files in |
| **Analyze** | What did they actually say that matters? | **Yes — the core** |
| Aggregate | Across many people, what's the pattern? | Later, if time |
| Deliver | How does someone consume it? | Stage 5 |

**The core problem restated:** getting an LLM to produce themes is easy. Getting themes **someone can trust** is the actual problem. LLMs fabricate plausible quotes and invent themes to fill a quota. Every decision below falls out of that.

**Example domain:** sales pipeline check-ins — an interviewer asks a rep about their Q4 deals. You know this world, so you can write realistic sample transcripts (be upfront that they're synthetic).

---

## 2. Build plan — something demo-able at every stage

Each stage has a **done when** and a **pitch if the interview happens now**.

### Stage 1 — Script: transcript file → themes JSON
- Parse a text file (`Interviewer:` / `Participant:` lines) into numbered turns.
- Send numbered turns to the LLM; get back themes, each with quotes as `{turn_id, text}`.
- Validate with Pydantic, **verify every quote in code**, print JSON.
- **Structure it as a pure core + thin shell** (D4): `analyze(transcript, llm) -> AnalysisResult` does the work; `cli.py` just reads the file and prints.
- **Done when:** `uv run python -m signal_lite.cli transcripts/rep_01.txt` prints valid JSON, and a fabricated quote gets dropped.
- **Pitch:** "The LLM call was the easy part. Here's how I stop it from making up evidence."

### Stage 2 — FastAPI: one endpoint
- `POST /analyze` — body: transcript text → response: `AnalysisResult`.
- Because Stage 1 already uses Pydantic models and a pure `analyze()`, this should be ~20 lines.
- **Done when:** `/docs` shows the endpoint with the real schema, and a test hits it with a fake LLM.
- **Pitch:** "Stage 2 was cheap because of how I structured Stage 1 — that's the abstraction argument."

### Stage 3 — Persist results in SQLite
- Store transcript, result, model name, prompt version, timestamp. Add `GET /analyses/{id}`.
- **Done when:** results survive a restart; you can tell which prompt produced which result.

### Stage 4 — Simple eval
- Golden set of 5–8 transcripts with hand-written expected themes, including traps (see §4).
- **Done when:** `uv run python -m evals.run` prints a scorecard you can compare across prompt versions.

### Stage 5 — Basic frontend
- React + TypeScript (their stack) via Vite: paste a transcript, see themes, click a theme to highlight its quotes in the transcript.

---

## 3. Decision log

Format: **Decision → Alternatives → Why → What would change my mind.**

### D1. Quotes are verified in code, not trusted from the model — *Stage 1*
- **Alternatives:** trust the model; ask the model to double-check itself.
- **Why:** the model is the thing that hallucinates, so it can't be the thing that checks. Asking for `turn_id` + text makes verification a cheap lookup: does this text appear in that turn (after normalizing whitespace/case)?
- **Unverified quotes are dropped, and the count is reported** (`dropped_quotes`). A theme with zero surviving quotes is dropped. Nothing is silently "fixed."
- **Quotes must come from participant turns.** If the interviewer said it and the rep said "yeah," that's a leading question, not evidence.
- **Would change my mind if:** paraphrased evidence turns out to matter — then fuzzy match + flag, still never unchecked.

### D2. Zero themes is a valid answer — *Stage 1*
- **Alternatives:** "Return 3–5 themes."
- **Why:** asking for N themes forces the model to invent themes when the conversation doesn't support them. The prompt asks for themes *the evidence supports*, and an empty list is allowed. "Not enough here to say" is a finding, not a failure.
- **Would change my mind if:** evals show the model under-reports real themes without a target count.

### D3. What the LLM returns ≠ what the system trusts — *Stage 1*
- **Why:** the LLM's output is a contract with an unreliable producer. Parse it into a `RawAnalysis` model, verify it, then build the trusted `AnalysisResult`. Use `model_validate_json` even if the SDK promises structured output — the model can still be wrong about content.
- On a parse failure: one retry with the validation errors fed back, then fail loudly.
- **Would change my mind if:** retries almost never help in evals → drop them.

```python
class Quote(BaseModel):
    turn_id: int
    text: str

class Theme(BaseModel):
    name: str
    summary: str
    quotes: list[Quote] = Field(min_length=1)

class AnalysisResult(BaseModel):
    themes: list[Theme]          # may be empty (D2)
    dropped_quotes: int          # unverified quotes removed (D1)
    model: str
    prompt_version: str
```

### D4. Pure core, thin shells — *Stage 1, pays off in Stage 2*
- **Why:** `analyze()` takes a transcript and an LLM client and returns data. It doesn't read files, print, or know about HTTP. The CLI (Stage 1), the API (Stage 2), and the eval runner (Stage 4) are all thin wrappers around the same function.
- **Would change my mind if:** the API needs behavior the CLI can't share (streaming, auth) — still lives in the shell, not the core.

### D5. Abstract the LLM. Don't abstract the database.
- **Why:** an abstraction should exist when there are already two real implementations. The LLM has two from the start: the real client and a `FakeLLM` that returns canned JSON (tests run offline, free, deterministic — including a canned *fabricated* quote to prove D1 works). The database has one: SQLite. A repository interface would be speculative.
  ```python
  class LLM(Protocol):
      def complete(self, prompt: str) -> str: ...
  ```
- **Would change my mind if:** a second storage backend becomes real.

### D6. `def`, not `async def`, for the endpoint (if the LLM client is sync) — *Stage 2*
- **Why:** FastAPI runs plain `def` endpoints in a threadpool. An `async def` endpoint that makes a blocking SDK call blocks the whole event loop, so every other request waits. Either use `def` with a sync client, or `async def` with the async client — never mix.
- **Would change my mind if:** you need to fan out concurrent LLM calls → async client + `asyncio.gather`.

### D7. SQLite, results as a JSON column — *Stage 3*
- **Alternatives:** Postgres; normalized `themes`/`quotes` tables.
- **Why:** zero infrastructure, one file, the stdlib ships it. Results are stored as the validated `AnalysisResult` JSON because nothing queries across individual themes yet. Store `model` + `prompt_version` with every row so any result can be traced to the prompt that made it.
- **Would change my mind if:** cross-transcript questions appear ("which themes show up for 30% of reps?") → normalize; or concurrent writers → Postgres.

### D8. No agent framework
- **Why:** this is one structured call. Calling the SDK directly keeps the prompt, retries, and validation visible — the exact parts worth discussing.
- **Would change my mind if:** the task needs multi-step tool use.

### D9. Deterministic eval metrics before LLM-as-judge — *Stage 4*
- **Why:** a judge model has its own errors to measure. Start with what code can check exactly; add a judge only for what code can't (does "budget risk" match "pricing concerns"?).

---

## 4. Eval design (Stage 4)

Golden set traps to include:
- **Small talk / off-topic** transcript → should return few or no themes (D2)
- **Leading question** — interviewer states the theme, rep just agrees → shouldn't count (D1)
- **Contradiction** — rep says the deal is solid, later describes a stalled champion
- **Confident but vague** — lots of energy, no specifics

Metrics:
- **Raw quote validity** — % of model quotes that pass verification *before* dropping. This is the model's real hallucination rate.
- **Theme recall** — did it find the themes you labeled? (manual or simple keyword match to start)
- **Stability** — run each transcript 3×; how much do the themes overlap? A measurement tool that gives different answers to the same input isn't measuring.
- **Tokens + latency per call** — cheap tracing.
- Track every metric by `prompt_version`.

---

## 5. What I'd do differently at Savo's scale
(Fill in after building — show you know the toy's limits.)
- Compare against human coders, not just my own labels
- Version prompts and models so results are reproducible months later
- Structured constructs + rubrics instead of open-ended themes, with explicit abstention when evidence is thin
- …
