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
2. Connects to **Fitbit**, **Renpho**, and **Hevy** to sync health & workout data
3. Stores encrypted fitness data in **PostgreSQL** (multi-source, tagged by `source`)
4. Provides a **React dashboard** for data visualization
5. Runs **daily automated syncs** via APScheduler

### User Flow

```
Login (Email/Google)  →  Connect Sources  →  Dashboard
         │                     │                │
    fastapi-users         Fitbit OAuth     React + Recharts
    JWT tokens            Renpho login     7/14/30 day views
                          Hevy API key
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
| Renpho | renpho-api (reverse-engineered cloud API) |
| Hevy | hevy-api (workout tracking) |
| Migrations | Alembic |

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
├── AGENTS.md                       # This file (symlinked as CLAUDE.md)
├── README.md                       # User documentation
├── docker-compose.yml              # All services
├── .env.example                    # Required environment variables
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py                      # FastAPI entry point + all routes
│   ├── tests/                      # pytest test suite
│   └── src/
│       ├── database.py             # SQLAlchemy async engine
│       ├── scheduler.py            # APScheduler daily sync (all sources)
│       ├── models/
│       │   └── db_models.py        # User, OAuthAccount, FitnessMetric
│       ├── services/
│       │   ├── user_service.py     # fastapi-users config + schemas
│       │   ├── token_encryption.py # Fernet encrypt/decrypt
│       │   ├── sync_utils.py       # Shared upsert_metric helper
│       │   ├── fitbit/
│       │   │   ├── client.py       # Fitbit API wrapper
│       │   │   └── sync.py         # Token refresh, disconnect
│       │   ├── renpho/
│       │   │   ├── client.py       # Renpho cloud API wrapper
│       │   │   └── sync.py         # Renpho sync logic
│       │   └── hevy/
│       │       ├── client.py       # Hevy API wrapper
│       │       └── sync.py         # Hevy sync logic
│       └── utils/
│           └── security.py         # OAuth state, input validation
│
├── frontend/
│   ├── Dockerfile                  # Multi-stage: build + Nginx
│   ├── nginx.conf                  # Nginx config for SPA routing
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
│           ├── LandingPage.tsx     # Public landing page (/)
│           ├── Dashboard.tsx       # Health dashboard (/dashboard)
│           ├── MuscleMap.tsx       # Interactive muscle heatmap (react-body-highlighter)
│           ├── Sources.tsx         # Connect Fitbit/Renpho/Hevy (/sources)
│           ├── AuthCallback.tsx    # OAuth callback handler
│           ├── Layout.tsx          # App shell (header/footer)
│           ├── SEO.tsx             # React Helmet meta tags
│           ├── About.tsx           # About page
│           ├── BlogIndex.tsx       # Blog listing
│           └── BlogPost.tsx        # Blog article
│
└── scripts/
    └── migrate_from_dynamodb.py    # One-time DynamoDB → PostgreSQL migration
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
| renpho_email | Text | Renpho account email |
| renpho_session_key | Text | Renpho session (encrypted) |
| hevy_api_key | Text | Hevy API key (Fernet-encrypted) |
| created_at | DateTime(tz) | |
| last_sync | DateTime(tz) | |

### Table: `oauth_account` (fastapi-users, Google OAuth tokens)

### Table: `fitness_metrics`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| user_id | UUID | FK → user.id |
| date | Date | |
| metric_type | String(32) | weight, sleep, activity, etc. |
| source | String(16) | fitbit, renpho, hevy |
| data | JSON | Metric-specific fields |
| synced_at | DateTime(tz) | |

**Unique constraint**: `(user_id, date, metric_type, source)`
**Indexes**: `(user_id, date)`, `(user_id, metric_type, date)`

### Metric Types

| Type | Source | Data Fields |
|------|--------|-------------|
| activity | fitbit | steps, calories_burned, distance_km, active_minutes, floors |
| sleep | fitbit | total_minutes, deep_minutes, light_minutes, rem_minutes, awake_minutes, efficiency |
| heart_rate | fitbit | resting_heart_rate, zones |
| weight | fitbit, renpho | weight_kg, bmi, body_fat_percent |
| hrv | fitbit | daily_rmssd, deep_rmssd |
| spo2 | fitbit | avg, min, max |
| breathing_rate | fitbit | breathing_rate |
| vo2_max | fitbit | vo2_max |
| temperature | fitbit | relative_deviation |
| active_zone_minutes | fitbit | fat_burn_minutes, cardio_minutes, peak_minutes, total_minutes |
| body_composition | renpho | muscle_mass, body_fat, water, bone_mass, protein, etc. |
| workout | hevy | exercises (with primary_muscle, secondary_muscles), volume, muscle_groups (weighted) |

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

### Tests

```bash
# Backend (from backend/)
source ../.venv/bin/activate
pytest                    # All tests
pytest -x                 # Stop on first failure
pytest --cov              # With coverage

# Frontend (from frontend/)
npm test                  # Vitest
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
| Fitbit | fitbit/client.py, fitbit/sync.py, app.py |
| Renpho | renpho/client.py, renpho/sync.py, app.py |
| Hevy | hevy/client.py, hevy/sync.py, app.py |
| Database | db_models.py, database.py |
| Dashboard | Dashboard.tsx, api.ts |
| Sources page | Sources.tsx, SourceIcons.tsx |
| Docker | docker-compose.yml, backend/Dockerfile |
| Tests | backend/tests/, conftest.py |

---

## External Docs

- [Fitbit Web API](https://dev.fitbit.com/build/reference/web-api/)
- [fastapi-users](https://fastapi-users.github.io/fastapi-users/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [React Query](https://tanstack.com/query/latest)
