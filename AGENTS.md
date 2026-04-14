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
| Auth | fastapi-users (JWT + Google OAuth) + Personal Access Tokens |
| Database | PostgreSQL + SQLAlchemy async |
| ORM | SQLAlchemy 2.0 (Mapped columns) |
| Encryption | cryptography (Fernet) for Fitbit tokens |
| Scheduling | APScheduler (daily sync at 06:00 UTC) |
| HTTP Client | httpx (async, for Fitbit API) |
| Renpho | renpho-api (reverse-engineered cloud API) |
| Hevy | hevy-api (workout tracking) |
| Migrations | Alembic |
| Rate Limiting | slowapi (token bucket, in-memory) |
| MCP Server | fastmcp (stdio transport for Claude Desktop) |

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
│   ├── mcp_server.py               # MCP stdio server for Claude Desktop (fastmcp)
│   ├── tests/                      # pytest test suite
│   └── src/
│       ├── database.py             # SQLAlchemy async engine
│       ├── scheduler.py            # APScheduler daily sync (all sources)
│       ├── api/v1/                  # Public API v1 (PAT + JWT auth)
│       │   ├── router.py           # Aggregates all v1 sub-routers
│       │   ├── vitals.py           # GET /api/v1/vitals (typed daily_vitals table)
│       │   ├── body.py             # GET /api/v1/body (typed body_measurements table)
│       │   ├── sleep.py            # GET /api/v1/sleep (typed daily_sleep table)
│       │   ├── activity.py         # GET /api/v1/activity (typed daily_activity table)
│       │   ├── intraday.py         # GET /api/v1/intraday (hourly_intraday table)
│       │   ├── exercises.py        # GET /api/v1/exercises (exercise_logs table)
│       │   ├── context.py          # GET /api/v1/context (user_context table)
│       │   ├── workouts.py         # GET /api/v1/workouts (typed workouts table)
│       │   ├── routines.py         # GET /api/v1/routines (typed routines table)
│       │   ├── recovery.py         # GET /api/v1/recovery
│       │   ├── tokens.py           # Token CRUD (JWT only)
│       │   └── audit.py            # Audit log (JWT only)
│       ├── auth/
│       │   ├── dependencies.py     # Dual auth: JWT + PAT
│       │   └── scopes.py           # Scope definitions (read:vitals, etc.)
│       ├── middleware/
│       │   ├── security_headers.py # HSTS, CSP, X-Frame-Options, no-cache
│       │   ├── rate_limit.py       # slowapi config (100/min PAT, 300 JWT)
│       │   └── audit.py            # Audit logging (fire-and-forget)
│       ├── models/
│       │   ├── db_models.py        # User, OAuthAccount, Base
│       │   ├── fitbit_models.py    # 7 typed Fitbit tables (daily_vitals, daily_sleep, etc.)
│       │   ├── hevy_models.py      # 3 typed Hevy tables (workouts, workout_exercises, routines)
│       │   ├── body_models.py      # BodyMeasurement (Renpho + Fitbit weight)
│       │   └── api_models.py       # APIToken, AuditLog
│       ├── schemas/
│       │   └── api_schemas.py      # Pydantic models for /api/v1/ responses
│       ├── services/
│       │   ├── user_service.py     # fastapi-users config + schemas
│       │   ├── token_service.py    # PAT generate, hash (SHA-256), validate, revoke
│       │   ├── token_encryption.py # Fernet encrypt/decrypt
│       │   ├── data_service.py     # Shared query logic (typed tables + legacy)
│       │   ├── audit_service.py    # Audit log writer
│       │   ├── sync_utils.py       # Shared _upsert generic helper
│       │   ├── fitbit_sync_utils.py # Typed upsert functions for Fitbit tables
│       │   ├── hevy_sync_utils.py  # Typed upsert functions for Hevy tables
│       │   ├── fitbit/
│       │   │   ├── client.py       # Fitbit API wrapper + data parsing
│       │   │   ├── sync.py         # Token refresh, disconnect
│       │   │   ├── stages.py       # Sleep stages 30s summary computation
│       │   │   ├── intraday.py     # Intraday hourly aggregation
│       │   │   ├── exercise_logs.py # Exercise log parsing
│       │   │   └── context.py      # Profile + device parsing
│       │   ├── renpho/
│       │   │   ├── client.py       # Renpho cloud API wrapper
│       │   │   └── sync.py         # Renpho sync logic
│       │   └── hevy/
│       │       ├── client.py       # Hevy API wrapper + workout parsing
│       │       ├── sync.py         # Hevy sync pipeline (typed tables + soft-delete)
│       │       └── routines.py     # Routine fetching and parsing
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
│           ├── Settings.tsx        # API token management (/settings)
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
| fitbit_intraday_available | Boolean | None=untested, True/False after first attempt |
| fitbit_scopes_version | Integer | Tracks OAuth scope version for re-auth prompts |
| created_at | DateTime(tz) | |
| last_sync | DateTime(tz) | |

### Table: `oauth_account` (fastapi-users, Google OAuth tokens)

### Typed Fitbit Tables (v2 — replaces fitness_metrics for Fitbit data)

**`daily_vitals`** — `(user_id, date, source)` unique. Columns: resting_heart_rate, hr_zones (JSONB), daily_rmssd, deep_rmssd, spo2_avg/min/max, breathing_rate, vo2_max, temp_relative_deviation.

**`daily_sleep`** — `(user_id, source, external_id)` unique. Multiple entries per day (main + naps). Columns: start_time, end_time, total/deep/light/rem/awake_minutes, efficiency, minutes_to_fall_asleep, time_in_bed, is_main_sleep, stages_30s_summary (JSONB).

**`daily_activity`** — `(user_id, date, source)` unique. Columns: steps, calories_burned, distance_km, active_minutes, sedentary_minutes, lightly_active_minutes, floors, calories_bmr, fat_burn/cardio/peak/total_azm.

**`daily_nutrition`** — Reserved (sync not implemented). Columns: calories_in, carbs/fat/protein/fiber_g, water_ml.

**`hourly_intraday`** — `(user_id, date, hour, metric_type, source)` unique. Columns: avg_value, min_value, max_value, sample_count, extra (JSONB).

**`exercise_logs`** — `(user_id, external_id, source)` unique. Columns: started_at, ended_at, activity_name, duration_minutes, avg_heart_rate, calories, distance_km, elevation_gain, speed_kmh, log_type, hr_zones (JSONB).

**`user_context`** — `(user_id, source)` unique. Columns: date_of_birth, gender, height_cm, timezone, utc_offset_ms, stride_length_walking/running, device_model, device_battery, last_device_sync.

### Typed Hevy Tables (v2 — replaces fitness_metrics for Hevy data)

**`workouts`** — `(user_id, external_id, source)` unique. Individual workouts (not per-day aggregates). Columns: title, description, started_at, ended_at, duration_minutes, total_volume_kg (working sets only, excludes warmup), total_sets, total_reps, muscle_groups (JSONB), deleted_at (soft-delete).

**`workout_exercises`** — FK to workouts.id (CASCADE). DELETE + re-INSERT per sync (no upsert). Columns: exercise_index, title, external_exercise_id, exercise_type, is_custom, supersets_id, notes, volume_kg, primary_muscle, secondary_muscles (JSONB), sets (JSONB).

**`routines`** — `(user_id, external_id, source)` unique. Planned workout templates. Columns: title, folder_id, exercises (JSONB with target sets/reps/weight).

### `body_measurements` (Renpho + Fitbit weight — consolidated)

`(user_id, source, measured_at)` unique. Supports intra-day measurements (morning + evening weigh-ins). Columns: weight_kg, bmi, body_fat_percent, body_water_percent, muscle_mass_percent, bone_mass_kg, bmr_kcal, visceral_fat, subcutaneous_fat_percent, protein_percent, body_age, lean_body_mass_kg, fat_free_weight_kg, heart_rate, cardiac_index, body_shape, sport_flag. Renpho fills all fields; Fitbit fills only weight_kg/bmi/body_fat_percent. `to_dict()` omits NULL fields for compact responses.

### Table: `api_tokens` (Personal Access Tokens)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| user_id | UUID | FK → user.id (CASCADE) |
| name | String(128) | User-defined label |
| token_hash | String(128) | SHA-256 of raw token (unique) |
| token_prefix | String(12) | First 12 chars for display (tonnd_xxxxxx) |
| scopes | JSON | e.g. ["read:vitals", "read:sleep"] |
| expires_at | DateTime(tz) | Nullable (null = no expiry) |
| last_used_at | DateTime(tz) | |
| created_at | DateTime(tz) | |
| revoked_at | DateTime(tz) | |
| is_active | Boolean | |

### Table: `audit_logs` (append-only)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | Primary key |
| user_id | UUID | FK → user.id (SET NULL) |
| token_id | UUID | FK → api_tokens.id (SET NULL) |
| action | String(64) | e.g. "api.get" |
| resource | String(256) | e.g. "/api/v1/vitals" |
| method | String(8) | GET, POST, etc. |
| ip_address | String(45) | |
| status_code | Integer | |
| created_at | DateTime(tz) | |

### Fitbit Data (typed tables)

| Table | Key Fields |
|-------|------------|
| daily_vitals | resting_heart_rate, hr_zones, daily_rmssd, deep_rmssd, spo2_avg/min/max, breathing_rate, vo2_max, temp_relative_deviation |
| daily_sleep | start_time, end_time, total/deep/light/rem/awake_minutes, efficiency, minutes_to_fall_asleep, time_in_bed, is_main_sleep, stages_30s_summary |
| daily_activity | steps, calories_burned, distance_km, active/sedentary/lightly_active_minutes, floors, calories_bmr, fat_burn/cardio/peak/total_azm |
| hourly_intraday | Hourly avg/min/max for heart_rate, hrv, spo2, steps, azm (opt-in, requires intraday API access) |
| exercise_logs | Fitbit activity logs with avg_heart_rate, hr_zones, speed_kmh, log_type, started_at, ended_at |
| user_context | date_of_birth, gender, height_cm, timezone, device_model, device_battery |

### Hevy Data (typed tables)

| Table | Key Fields |
|-------|------------|
| workouts | title, description, started_at, ended_at, duration_minutes, total_volume_kg (excludes warmup), muscle_groups, deleted_at (soft-delete) |
| workout_exercises | exercise_index, title, exercise_type, is_custom, supersets_id, notes, volume_kg, primary_muscle, secondary_muscles, sets |
| routines | title, folder_id, exercises (JSONB with planned sets/reps/weight) |

### Body Data (body_measurements table — Renpho + Fitbit)

| Source | Fields |
|--------|--------|
| renpho | weight_kg, bmi, body_fat_percent, body_water_percent, muscle_mass_percent, bone_mass_kg, bmr_kcal, visceral_fat, subcutaneous_fat_percent, protein_percent, body_age, lean_body_mass_kg, fat_free_weight_kg, heart_rate, cardiac_index, body_shape, sport_flag |
| fitbit | weight_kg, bmi, body_fat_percent |

---

## Security

- **Auth**: fastapi-users with JWT (1h expiry) + Personal Access Tokens (scoped, revocable, SHA-256 hashed). Secrets must be set via env vars — app refuses to start without `JWT_SECRET`, `RESET_PASSWORD_TOKEN_SECRET`, `VERIFICATION_TOKEN_SECRET`.
- **PATs**: `tonnd_` prefix, 256-bit entropy, max 25 per user. Token hash stored (not raw). Scopes: `read:vitals`, `read:body`, `read:sleep`, `read:activity`, `read:workouts`, `read:recovery`, `read:all`.
- **Encryption**: Fitbit OAuth tokens encrypted at rest with Fernet. `ENCRYPTION_KEY` required.
- **OAuth State**: HMAC-SHA256 signed, 10-minute expiry.
- **CORS**: Restricted to `FRONTEND_URL`, explicit `allow_headers` (Authorization, Content-Type).
- **Rate Limiting**: slowapi — 100 req/min (PAT), 300 req/min (JWT), 10 req/min (unauth).
- **Security Headers**: HSTS, CSP, X-Frame-Options DENY, no-cache on /api/ endpoints.
- **Audit Logging**: All /api/v1/ access logged (append-only `audit_logs` table).

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
| Public API v1 | api/v1/router.py, auth/dependencies.py, auth/scopes.py |
| API Tokens (PATs) | token_service.py, api/v1/tokens.py, Settings.tsx |
| MCP Server | mcp/remote_server.py |
| Fitbit sync | scheduler.py (sync functions), fitbit/client.py, fitbit_sync_utils.py |
| Fitbit models | fitbit_models.py (8 typed tables), data_service.py (queries) |
| Fitbit parsing | fitbit/stages.py, fitbit/intraday.py, fitbit/exercise_logs.py, fitbit/context.py |
| Renpho sync | renpho/client.py, renpho/sync.py, sync_utils.py (upsert_body_measurement) |
| Body models | body_models.py (BodyMeasurement), data_service.py (query_body_measurements) |
| Hevy sync | scheduler.py (sync functions), hevy/client.py, hevy_sync_utils.py |
| Hevy models | hevy_models.py (3 typed tables), data_service.py (queries) |
| Hevy parsing | hevy/routines.py, hevy/client.py (_workout_to_metrics, _fetch_template_info) |
| Database | db_models.py, fitbit_models.py, hevy_models.py, body_models.py, api_models.py, database.py |
| Dashboard | Dashboard.tsx, api.ts |
| Sources page | Sources.tsx, SourceIcons.tsx |
| Security/Middleware | middleware/security_headers.py, middleware/rate_limit.py, middleware/audit.py |
| Docker | docker-compose.yml, backend/Dockerfile |
| Tests | backend/tests/, conftest.py |

---

## External Docs

- [Fitbit Web API](https://dev.fitbit.com/build/reference/web-api/)
- [fastapi-users](https://fastapi-users.github.io/fastapi-users/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [React Query](https://tanstack.com/query/latest)
