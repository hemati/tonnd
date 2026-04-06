# AGENTS.md - TONND

> Context for AI agents (Claude, Cursor, Copilot, etc.) to understand this project.

## Project Overview

**Project**: TONND
**Repo**: https://github.com/hemati/tonnd
**Status**: Early Alpha (v0.2.0) - Docker-based, open source
**Stack**: FastAPI + PostgreSQL + React + Docker

### What It Does

An open-source fitness tracking platform that:
1. Authenticates users via **Email/Password** or **Google OAuth** (fastapi-users)
2. Connects to **Fitbit API** to sync health data (weight, sleep, activity, HRV, SpO2, etc.)
3. Stores encrypted fitness data in **PostgreSQL**
4. Provides a **React dashboard** for data visualization
5. Runs **daily automated syncs** via APScheduler

### User Flow

```
Login (Email/Google)  →  Connect Fitbit  →  Dashboard
         │                     │                │
    fastapi-users         OAuth 2.0        React + Recharts
    JWT tokens            Fitbit API       7/14/30 day views
```

---

## Tech Stack

### Backend (Python 3.12)

| Component | Technology |
|-----------|------------|
| Framework | FastAPI + uvicorn |
| Auth | fastapi-users (JWT + Google OAuth) |
| Database | PostgreSQL + SQLAlchemy async |
| ORM | SQLAlchemy 2.0 (Mapped columns) |
| Encryption | cryptography (Fernet) for Fitbit tokens |
| Scheduling | APScheduler (daily sync at 06:00 UTC) |
| HTTP Client | httpx (async, for Fitbit API) |
| Migrations | Alembic (not yet initialized) |

### Frontend (TypeScript + React 18)

| Component | Technology |
|-----------|------------|
| Build | Vite |
| Styling | Tailwind CSS |
| Charts | Recharts |
| Data Fetching | @tanstack/react-query |
| HTTP Client | Axios |
| Icons | @heroicons/react |
| UI Primitives | Radix UI |
| Routing | React Router v6 |

### Infrastructure

| Component | Technology |
|-----------|------------|
| Orchestration | Docker Compose |
| Database | PostgreSQL 16 (Docker) |
| Backend | Python 3.12 container |
| Frontend | Node 18 container (Vite dev server) |

---

## Project Structure

```
tonnd/
├── AGENTS.md                       # This file
├── README.md                       # User documentation
├── docker-compose.yml              # All services
├── .env.example                    # Required environment variables
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py                      # FastAPI entry point + all routes
│   └── src/
│       ├── database.py             # SQLAlchemy async engine
│       ├── scheduler.py            # APScheduler daily sync
│       ├── models/
│       │   └── db_models.py        # User + FitnessMetric tables
│       ├── services/
│       │   ├── user_service.py     # fastapi-users config + schemas
│       │   ├── fitbit_client.py    # Fitbit API wrapper
│       │   ├── fitbit_sync.py      # Shared helpers (token refresh, upsert)
│       │   └── token_encryption.py # Fernet encrypt/decrypt
│       └── utils/
│           └── security.py         # OAuth state, input validation
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── main.tsx                # Entry point
│       ├── App.tsx                 # Routing
│       ├── config/
│       │   └── constants.ts        # API_URL, TOKEN_KEY
│       ├── hooks/
│       │   └── useAuth.ts          # JWT auth (localStorage)
│       ├── services/
│       │   └── api.ts              # Axios client + API functions
│       └── components/
│           ├── Login.tsx           # Google + Email/Password login
│           ├── Dashboard.tsx       # Health dashboard
│           ├── FitbitConnect.tsx   # Fitbit OAuth flow
│           ├── AuthCallback.tsx   # OAuth callback handler
│           └── Layout.tsx         # App shell
│
└── .github/                        # (to be created)
```

---

## Database Schema (PostgreSQL)

### Table: `user` (fastapi-users base + custom fields)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| email | String | Unique |
| hashed_password | String | Argon2 hash |
| is_active | Boolean | |
| fitbit_user_id | String | Fitbit user ID |
| fitbit_access_token | Text | Fernet-encrypted |
| fitbit_refresh_token | Text | Fernet-encrypted |
| fitbit_token_expires | Integer | Unix timestamp |
| created_at | DateTime(tz) | |
| last_sync | DateTime(tz) | |

### Table: `fitness_metrics`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| user_id | UUID | FK → user.id |
| date | Date | |
| metric_type | String(32) | weight, sleep, activity, etc. |
| data | JSON | Metric-specific fields |
| synced_at | DateTime(tz) | |

**Unique constraint**: `(user_id, date, metric_type)`
**Indexes**: `(user_id, date)`, `(user_id, metric_type, date)`

### Metric Types

| Type | Data Fields |
|------|-------------|
| activity | steps, calories_burned, distance_km, active_minutes, floors |
| sleep | total_minutes, deep_minutes, light_minutes, rem_minutes, awake_minutes, efficiency |
| heart_rate | resting_heart_rate, zones |
| weight | weight_kg, bmi, body_fat_percent |
| hrv | daily_rmssd, deep_rmssd |
| spo2 | avg, min, max |
| breathing_rate | breathing_rate |
| vo2_max | vo2_max |
| temperature | relative_deviation |
| active_zone_minutes | fat_burn_minutes, cardio_minutes, peak_minutes, total_minutes |

---

## Security

- **Auth**: fastapi-users with JWT (1h expiry). Secrets must be set via env vars — app refuses to start without `JWT_SECRET`, `RESET_PASSWORD_TOKEN_SECRET`, `VERIFICATION_TOKEN_SECRET`.
- **Encryption**: Fitbit OAuth tokens encrypted at rest with Fernet. `ENCRYPTION_KEY` required.
- **OAuth State**: HMAC-SHA256 signed, 10-minute expiry.
- **CORS**: Restricted to `FRONTEND_URL`.

---

## Development

### Quick Start

```bash
cp .env.example .env
# Edit .env — set JWT_SECRET, ENCRYPTION_KEY, etc.
docker compose up
# Frontend: http://localhost:5173
# Backend:  http://localhost:8080
# API Docs: http://localhost:8080/docs
```

### Without Docker

```bash
# Backend
cd backend
source ../.venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8080

# Frontend
cd frontend
npm install
npm run dev
```

### Code Quality

```bash
# Backend
ruff check .              # Lint
ruff format .             # Format

# Frontend
npm run lint              # ESLint
npx tsc --noEmit          # Type check
```

---

## Key Files for AI Agents

| Working on... | Start with |
|---------------|------------|
| Auth | user_service.py, useAuth.ts |
| Fitbit Sync | fitbit_client.py, fitbit_sync.py, app.py (sync endpoint) |
| Database | db_models.py, database.py |
| Dashboard | Dashboard.tsx, api.ts |
| Docker | docker-compose.yml, backend/Dockerfile |

---

## External Docs

- [Fitbit Web API](https://dev.fitbit.com/build/reference/web-api/)
- [fastapi-users](https://fastapi-users.github.io/fastapi-users/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [React Query](https://tanstack.com/query/latest)
