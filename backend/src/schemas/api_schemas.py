"""Pydantic models for the /api/v1/ public API.

Inspired by open-wearables schema patterns: typed fields, units in names,
Field descriptions for OpenAPI docs.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ─── Pagination ──────────────────────────────────────────────────────────────


class PaginatedResponse(BaseModel):
    count: int = Field(..., description="Number of items in this response")
    data: list[dict]


# ─── Metric responses (typed per category) ───────────────────────────────────


class VitalsEntry(BaseModel):
    """A single vitals data point (HR, HRV, SpO2, etc.)."""

    date: str
    metric_type: str
    source: str
    resting_heart_rate: int | None = Field(None, description="Resting HR in bpm")
    daily_rmssd: float | None = Field(None, description="HRV RMSSD in ms")
    avg: float | None = Field(None, description="SpO2 average %")
    breathing_rate: float | None = Field(None, description="Breaths per minute")
    vo2_max: float | None = Field(None, description="VO2 Max in mL/kg/min")
    relative_deviation: float | None = Field(None, description="Skin temp deviation in C")

    model_config = ConfigDict(extra="allow")


class SleepEntry(BaseModel):
    """A single sleep record."""

    date: str
    metric_type: str = "sleep"
    source: str
    total_minutes: int | None = Field(None, description="Total sleep duration")
    deep_minutes: int | None = Field(None, description="Deep sleep minutes")
    light_minutes: int | None = Field(None, description="Light sleep minutes")
    rem_minutes: int | None = Field(None, description="REM sleep minutes")
    awake_minutes: int | None = Field(None, description="Awake minutes")
    efficiency: int | None = Field(None, ge=0, le=100, description="Sleep efficiency %")

    model_config = ConfigDict(extra="allow")


class BodyEntry(BaseModel):
    """A single body composition measurement."""

    date: str
    metric_type: str
    source: str
    weight_kg: float | None = Field(None, description="Weight in kg")
    bmi: float | None = Field(None, description="Body mass index")
    body_fat_percent: float | None = Field(None, description="Body fat %")
    muscle_mass_kg: float | None = Field(None, description="Muscle mass in kg")

    model_config = ConfigDict(extra="allow")


class ActivityEntry(BaseModel):
    """A single activity/steps record."""

    date: str
    metric_type: str
    source: str
    steps: int | None = Field(None, description="Total step count")
    calories_burned: int | None = Field(None, description="Total calories")
    distance_km: float | None = Field(None, description="Distance in km")
    active_minutes: int | None = Field(None, description="Active minutes")

    model_config = ConfigDict(extra="allow")


class WorkoutEntry(BaseModel):
    """A single workout record from Hevy."""

    date: str
    metric_type: str = "workout"
    source: str = "hevy"
    title: str | None = Field(None, description="Workout title")
    workout_count: int | None = Field(None, description="Number of workouts that day")
    duration_minutes: float | None = Field(None, description="Duration in minutes")
    total_volume_kg: float | None = Field(None, description="Total volume lifted in kg")
    total_sets: int | None = Field(None, description="Total sets performed")
    total_reps: int | None = Field(None, description="Total reps performed")
    exercises: list[dict] | None = Field(None, description="Exercise details with sets/reps/weight")
    muscle_groups: dict[str, float] | None = Field(
        None,
        description="Weighted muscle group breakdown (primary=1.0, secondary=0.4)",
    )

    model_config = ConfigDict(extra="allow")


# ─── Recovery ────────────────────────────────────────────────────────────────


class RecoveryResponse(BaseModel):
    """Recovery score computed from HRV, sleep efficiency, and resting HR.

    Formula: 40% HRV + 35% sleep efficiency + 25% resting HR.
    """

    score: int | None = Field(None, ge=0, le=100, description="Overall recovery 0-100")
    hrv_score: float | None = Field(None, description="HRV component score")
    sleep_score: float | None = Field(None, description="Sleep efficiency component")
    rhr_score: float | None = Field(None, description="Resting HR component")
    latest_hrv: dict | None = None
    latest_sleep: dict | None = None
    latest_hr: dict | None = None


# ─── Token management ────────────────────────────────────────────────────────


class TokenCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, pattern=r"^[\w\s\-\.]+$")
    scopes: list[str] = Field(default=["read:all"])
    expires_at: datetime | None = Field(None, description="Optional expiry (null = no expiry)")


class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    token_prefix: str = Field(..., description="First 12 chars for identification")
    scopes: list[str]
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime
    is_active: bool


class TokenCreateResponse(BaseModel):
    token: str = Field(..., description="Raw token — shown only once. Store securely.")
    id: UUID
    name: str
    scopes: list[str]
    expires_at: datetime | None
    created_at: datetime


# ─── Audit ────────────────────────────────────────────────────────────────────


class AuditEntry(BaseModel):
    id: UUID
    action: str
    resource: str | None = None
    method: str | None = None
    ip_address: str | None = None
    status_code: int | None = None
    created_at: datetime


class AuditListResponse(BaseModel):
    count: int = Field(..., description="Total audit entries for this user")
    data: list[AuditEntry]
