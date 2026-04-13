"""Main v1 API router — aggregates all sub-routers."""

from fastapi import APIRouter

from src.api.v1 import (
    activity,
    audit,
    body,
    context,
    exercises,
    intraday,
    metrics,
    recovery,
    routines,
    sleep,
    tokens,
    vitals,
    workouts,
)

router = APIRouter(prefix="/api/v1", tags=["api-v1"])

router.include_router(vitals.router)
router.include_router(body.router)
router.include_router(sleep.router)
router.include_router(activity.router)
router.include_router(workouts.router)
router.include_router(routines.router)
router.include_router(recovery.router)
router.include_router(metrics.router)
router.include_router(intraday.router)
router.include_router(exercises.router)
router.include_router(context.router)
router.include_router(tokens.router)
router.include_router(audit.router)
