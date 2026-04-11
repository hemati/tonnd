# TONND

[![Tests](https://github.com/hemati/tonnd/actions/workflows/tests.yml/badge.svg)](https://github.com/hemati/tonnd/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/hemati/tonnd/graph/badge.svg)](https://codecov.io/gh/hemati/tonnd)
[![Discord](https://img.shields.io/badge/Discord-Join%20Community-5865F2?logo=discord&logoColor=white)](https://discord.gg/3qmrFpwzpE)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)

Open-source, self-hosted health dashboard. Connect Fitbit, Renpho, and Hevy — see all your metrics in one place. Runs entirely in Docker.

## Features

- **Google + Email/Password Login** via fastapi-users
- **Fitbit Integration** - Sleep, activity, heart rate, HRV, SpO2, VO2 Max, breathing rate, skin temperature, active zone minutes
- **Renpho Integration** - Weight, body composition (body fat, muscle mass, water, bone mass)
- **Hevy Integration** - Workout tracking (exercises, sets, reps, volume)
- **Recovery Score** - Calculated from HRV, sleep efficiency, and resting heart rate
- **Daily Auto-Sync** - APScheduler runs at 06:00 UTC
- **Historical Sync** - Up to 30 days retroactively
- **React Dashboard** - Interactive charts with Recharts (7/14/30 day views)

## Quick Start

```bash
git clone https://github.com/hemati/tonnd.git
cd tonnd
cp .env.example .env
# Edit .env - set JWT_SECRET, ENCRYPTION_KEY (see .env.example for instructions)
docker compose up
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy async |
| Auth | fastapi-users (JWT, Google OAuth) |
| Database | PostgreSQL 16 |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Charts | Recharts |
| Infrastructure | Docker Compose |

## Project Structure

```
backend/
  app.py                  # FastAPI server + routes
  src/
    database.py           # SQLAlchemy engine
    scheduler.py          # Daily sync (all sources)
    models/db_models.py   # User, OAuthAccount, FitnessMetric
    services/
      user_service.py     # Auth config (fastapi-users)
      sync_utils.py       # Shared upsert helper
      token_encryption.py # Fernet encryption
      fitbit/             # Fitbit API client + sync
      renpho/             # Renpho API client + sync
      hevy/               # Hevy API client + sync

frontend/
  src/
    App.tsx               # Routing
    hooks/useAuth.ts      # JWT auth
    services/api.ts       # API client
    components/
      Login.tsx           # Login page
      Dashboard.tsx       # Health dashboard
      Sources.tsx         # Connect data sources
```

## Environment Variables

See [.env.example](.env.example) for all required variables. Key ones:

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET` | Yes | Signs JWT tokens (app refuses to start without it) |
| `ENCRYPTION_KEY` | Yes | Fernet key for encrypting Fitbit tokens at rest |
| `GOOGLE_CLIENT_ID` | No | For Google OAuth login (email/password works without it) |
| `FITBIT_CLIENT_ID` | No | For Fitbit sync (dashboard works without it, just no data) |
| `RENPHO_*` | No | Renpho credentials (connected per-user via UI) |
| `HEVY_*` | No | Hevy API key (connected per-user via UI) |

## Development

```bash
# Backend (without Docker)
cd backend
source ../.venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --port 8080

# Frontend (without Docker)
cd frontend
npm install
npm run dev

# Tests
cd backend && pytest
cd frontend && npm test

# Code quality
cd backend && ruff check . && ruff format .
cd frontend && npm run lint && npx tsc --noEmit
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[AGPL-3.0](LICENSE) — If you modify or deploy this software, you must make your source code available.
