# Contributing to TONND

Thanks for your interest in contributing!

## Quick Start

```bash
git clone https://github.com/hemati/tonnd.git
cd tonnd
cp .env.example .env
# Edit .env (see .env.example for instructions)
docker compose up
```

Frontend: http://localhost:5173 | Backend: http://localhost:8080 | API Docs: http://localhost:8080/docs

## Development Without Docker

```bash
# Backend
cd backend
python -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --port 8080

# Frontend
cd frontend
npm install
npm run dev
```

## Code Quality

Run these before committing:

```bash
# Backend
cd backend
ruff check .        # Lint
ruff format .       # Format

# Frontend
cd frontend
npm run lint        # ESLint
npx tsc --noEmit   # Type check
```

## Pull Request Process

1. Fork the repo and create a feature branch from `main`
2. Make your changes
3. Run lint + type checks (see above)
4. Test manually: `docker compose up` and verify your changes work
5. Open a PR with a clear description of what you changed and why

## What to Work On

Check the [issues](https://github.com/hemati/tonnd/issues) for open tasks. Good first issues are labeled accordingly.

## Architecture Notes

- **Backend**: FastAPI with fastapi-users for auth, SQLAlchemy async for DB
- **Frontend**: React 18 + TypeScript, no state management library (React Query handles server state)
- **Auth**: JWT tokens stored in localStorage, Google OAuth optional
- **Fitbit tokens**: Encrypted at rest with Fernet

See [AGENTS.md](AGENTS.md) for the full architecture reference.
