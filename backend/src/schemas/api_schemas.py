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


# ─── V2 schemas (typed tables) ──────────────────────────────────────────────


class SleepEntryV2(BaseModel):
    """Extended sleep record with start/end time, onset latency, and stages."""
    date: str
    source: str
    external_id: str
    start_time: str | None = None
    end_time: str | None = None
    total_minutes: int | None = None
    deep_minutes: int | None = None
    light_minutes: int | None = None
    rem_minutes: int | None = None
    awake_minutes: int | None = None
    efficiency: int | None = None
    minutes_to_fall_asleep: int | None = None
    time_in_bed: int | None = None
    is_main_sleep: bool | None = None
    stages_30s_summary: dict | None = None


class ActivityEntryV2(BaseModel):
    """Extended activity record with sedentary, light active, BMR, and AZM."""
    date: str
    source: str
    steps: int | None = None
    calories_burned: int | None = None
    distance_km: float | None = None
    active_minutes: int | None = None
    sedentary_minutes: int | None = None
    lightly_active_minutes: int | None = None
    floors: int | None = None
    calories_bmr: int | None = None
    fat_burn_azm: int | None = None
    cardio_azm: int | None = None
    peak_azm: int | None = None
    total_azm: int | None = None


class VitalsEntryV2(BaseModel):
    """All vitals in a single row."""
    date: str
    source: str
    resting_heart_rate: float | None = None
    hr_zones: dict | None = None
    daily_rmssd: float | None = None
    deep_rmssd: float | None = None
    spo2_avg: float | None = None
    spo2_min: float | None = None
    spo2_max: float | None = None
    breathing_rate: float | None = None
    vo2_max: float | None = None
    temp_relative_deviation: float | None = None


class IntradayEntry(BaseModel):
    """Hourly intraday summary."""
    date: str
    hour: int
    metric_type: str
    source: str
    avg_value: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    sample_count: int | None = None
    extra: dict | None = None


class ExerciseLogEntry(BaseModel):
    """Fitbit exercise log (cardio session)."""
    date: str
    source: str
    external_id: str
    started_at: str | None = None
    ended_at: str | None = None
    activity_name: str | None = None
    duration_minutes: int | None = None
    avg_heart_rate: int | None = None
    calories: int | None = None
    distance_km: float | None = None
    elevation_gain: float | None = None
    speed_kmh: float | None = None
    log_type: str | None = None
    hr_zones: list[dict] | None = None


class UserContextEntry(BaseModel):
    """User profile + device context."""
    source: str
    date_of_birth: str | None = None
    age: int | None = Field(None, description="Computed from date_of_birth")
    gender: str | None = None
    height_cm: float | None = None
    timezone: str | None = None
    device_model: str | None = None
    device_battery: int | None = None
    last_device_sync: str | None = None


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


# ─── Hevy V2 schemas (typed tables) ───────────────────────────────────────────


class WorkoutExerciseEntry(BaseModel):
    exercise_index: int
    title: str | None = None
    external_exercise_id: str | None = None
    exercise_type: str | None = None
    is_custom: bool | None = None
    supersets_id: int | None = None
    notes: str | None = None
    volume_kg: float | None = None
    primary_muscle: str | None = None
    secondary_muscles: list[str] | None = None
    sets: list[dict] | None = None


class WorkoutResponseV2(BaseModel):
    date: str
    source: str
    external_id: str
    title: str | None = None
    description: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    duration_minutes: int | None = None
    total_volume_kg: float | None = None
    total_sets: int | None = None
    total_reps: int | None = None
    muscle_groups: dict | None = None
    exercises: list[WorkoutExerciseEntry] | None = None


class RoutineEntry(BaseModel):
    source: str
    external_id: str
    title: str | None = None
    folder_id: int | None = None
    exercises: list[dict] | None = None
