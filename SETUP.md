# Setup

## Prerequisites

- Python 3.11+
- Node.js 20+ and npm
- Docker and Docker Compose (optional, for the containerized workflow)

## Option A: Docker Compose (recommended for a full stack quickly)

```bash
git clone <repository-url> teklini-nexora
cd teklini-nexora
docker compose up --build
```

This starts three containers:

- `backend` — FastAPI on `http://localhost:8000`, backed by PostgreSQL
- `frontend` — the built React app served by nginx on `http://localhost:8080`
- `db` — PostgreSQL 16

Once the containers report healthy, open `http://localhost:8080` and submit the demo incident
from the dashboard.

## Option B: Local development (SQLite, hot reload)

### Backend

Linux/macOS:

```bash
python3 --version  # must satisfy >= 3.11
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp .env.example .env
python -m uvicorn nexora.api.main:app --reload --port 8000
```

Windows PowerShell:

```powershell
py --version  # must satisfy >= 3.11
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m uvicorn nexora.api.main:app --reload --port 8000
```

The `.env` file is ignored by git; never commit real API keys or database credentials. The
documented Python requirement is the repository requirement from `pyproject.toml` (`>=3.11`);
Python 3.11 through 3.14 are the practical versions currently exercised locally.

The API is now available at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`. A local `nexora.db` SQLite file is created automatically on first
run.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The dashboard is available at `http://localhost:5173`. Vite proxies `/api/*` requests to
`http://localhost:8000` (configured in `frontend/vite.config.ts`), so both servers need to be
running.

## Running tests

```bash
python -m pip install -e "[dev]"
python -m pytest
```

The standard suite forces deterministic heuristic mode even when a local `.env` contains Gemini
settings. The live provider smoke test is excluded from normal discovery and must be selected
explicitly:

```bash
python -m pytest tests/live -m live_gemini -o addopts=""
```

It is skipped when `GOOGLE_API_KEY` is absent, has a bounded provider timeout, and reports provider
failures without printing credentials.

Frontend tests and production build:

```bash
cd frontend
npm install
npm test
npm run build
```

## Demo and authenticated mode

With the backend and frontend running, use **Run demo investigation** in the dashboard. The same
flow is available through the API:

```bash
curl -X POST http://localhost:8000/api/incidents \
  -H "Content-Type: application/json" \
  -d '{"use_demo_data": true}'
```

For authenticated mode, set these values in `.env` before starting the backend:

```env
NEXORA_AUTH_REQUIRED=true
NEXORA_API_KEY=<set-locally>
NEXORA_SECRET_KEY=<set-a-different-local-secret>
```

The frontend accepts the API key in the sidebar and keeps it in browser session storage. For
direct API calls, send `X-API-Key: <your-local-api-key>`. This is a prototype API
boundary, not a complete identity, TLS, rate-limiting, or audit system.

## Simple development workflow

Use two terminals after the one-time setup: run `python -m uvicorn nexora.api.main:app --reload
--port 8000` from the repository root, then run `npm run dev` from `frontend`. There is no
verified cross-platform single-command launcher in this repository, so Docker and one-command
startup are documented separately rather than claimed as tested portability guarantees.

Run the evaluation harness separately:

```bash
python -m nexora.evaluation.run_eval
```

Run frontend linting:

```bash
cd frontend
npm run lint
```

## Running against PostgreSQL locally (without Docker)

```bash
pip install -e ".[dev,postgres]"
export DATABASE_URL="postgresql+psycopg://nexora:nexora@localhost:5432/nexora"
uvicorn nexora.api.main:app --reload
```

Tables are created automatically on startup via `init_db()`; for schema evolution beyond the
initial version, introduce Alembic migrations (the dependency is already included).

## Enabling Gemini-backed reasoning

By default, Nexora runs entirely on deterministic heuristic reasoning and makes no external model
calls. To route free-text reasoning through Gemini instead:

```bash
pip install -e ".[adk]"
```

```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your-key-here
GEMINI_MODEL=gemini-2.0-flash
```

## API protection

Local demo mode leaves authentication disabled so the dashboard works immediately. Before any
shared or deployed environment, set `NEXORA_AUTH_REQUIRED=true` and provide a strong
`NEXORA_API_KEY`. Clients can send it as `X-API-Key` or as a Bearer token. This is a minimal API
boundary for the prototype, not a replacement for an identity provider, TLS termination, rate
limiting, audit logging, and network policy.

## Troubleshooting

- **`ModuleNotFoundError: No module named 'nexora'`** — make sure you installed the package with
  `pip install -e .` (editable mode) from the repository root, and that `pythonpath = ["src"]` in
  `pyproject.toml`'s `[tool.pytest.ini_options]` is intact if running tests directly.
- **Frontend requests to `/api/*` return connection errors** — confirm the backend is running on
  port 8000; the Vite dev server proxy expects it there.
- **SQLite "database is locked" errors under load** — this is expected under SQLite's
  single-writer model. Switch to PostgreSQL via `DATABASE_URL` for concurrent workloads.
