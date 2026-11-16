# WordMate AI

An English vocabulary learning MVP built with **FastAPI, SQLite, Docker, and vanilla JavaScript**. Look up structured English dictionary definitions, save words, and practice four-choice quizzes.

## Features

- **Dictionary** — English definitions grouped by actual parts of speech, sourced from [Free Dictionary API](https://dictionaryapi.dev/). Examples appear when the source provides them; missing examples are not fabricated.
- **My Words** — Save words with case-insensitive duplicate prevention, expand/collapse explanations, and delete saved items.
- **Quiz** — Generate four-choice questions from saved definitions, check answers server-side, and track current-session score.
- **Mobile-friendly** interface, with three navigation sections.
- **Optional** legacy `/chat` Ollama endpoint; dictionary lookups no longer require Ollama inference.

## Architecture

```
Browser (HTML/CSS/JS)
    |  REST JSON
FastAPI (api container)
    |-- SQLite (/data/vocabulary.db, named Docker volume)
    |-- HTTPS --> Free Dictionary API (dictionaryapi.dev)
    `-- optional --> Ollama /api/chat (development compose)
```

## Run

Requirements: Docker Desktop / Docker Compose. Port 8001 must be available. Internet access is required to look up dictionary entries.

```bash
docker compose up -d --build
```

Open **http://localhost:8001/**. Swagger docs: **http://localhost:8001/docs**. Health: **http://localhost:8001/health**.

For local code hot reload, use an existing external Ollama volume or adjust/remove that service in `compose.dev.yaml`:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up -d --build
```

The optional Ollama service in the development Compose references an **existing** external volume named `ai-model-serving_ollama_data`. Use plain `docker compose up` if that volume is unavailable.

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health |
| POST | `/vocabulary/explain` | Lookup dictionary JSON (`word`) |
| POST | `/vocabulary/save` | Save `word` and structured `explanation` |
| GET | `/vocabulary/saved` | List saved words |
| DELETE | `/vocabulary/{id}` | Remove saved word |
| GET | `/quiz/question` | Four-choice quiz question (min 4 words) |
| POST | `/quiz/answer` | Evaluate `question_id`, `answer` |
| POST | `/chat` | Optional Ollama chat |

## Reset only vocabulary test records

The following **permanently removes saved vocabulary** but keeps the SQLite table, named volume, and Ollama models:

```bash
docker compose exec api python -c "from app.database import clear_test_words; print('Deleted:',clear_test_words())"
```

When using dev compose, add `-f compose.yaml -f compose.dev.yaml` before `exec`. **Never use `docker compose down -v` for this purpose** because it removes named volumes.

## Data contract

SQLite stores `explanation` as JSON text with `word`, `meanings[]`, `partOfSpeech`, `definitions[]`, `definition`, and optional `example`. `GET /vocabulary/saved` also returns parsed `dictionary` values. Old plain-text saves can still be displayed, but new saves require structured JSON.

## Limitations

- The public API is third-party and requires connectivity; reliability and licensing should be reviewed before commercial deployment.
- Dictionary entries may lack examples or common collocations; the app does not invent them. Collocations are intentionally omitted in this version.
- Quiz questions are randomly selected; repeats across questions are possible, and score resets upon reload.
- The quiz API uses saved word IDs rather than authentication/session-bound quiz tokens. Suitable for a personal MVP, not high-stakes testing.
- No login or per-user isolation. Do not expose publicly without access control and additional hardening.

## Test

```bash
python -m pip install pytest
PYTHONPATH=. pytest -q
```

## Planned extensions

Quiz sessions without repeated questions; spaced repetition; account support; dictionary caching; standardized source attribution and licensing.
