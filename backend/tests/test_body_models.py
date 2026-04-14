"""Tests for body_measurements table — schema, constraints, to_dict, and upserts."""

import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import select

from src.models.body_models import BodyMeasurement
from src.services.sync_utils import upsert_body_measurement

from tests.conftest import test_session_maker


# ─── Model CRUD & Constraints ──────────────────────────────────────


@pytest.mark.asyncio
class TestBodyMeasurement:
    async def test_insert_and_read_renpho(self):
        """Insert a Renpho measurement with cardiac_index and sport_flag."""
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            ts = datetime(2026, 4, 13, 8, 30, tzinfo=timezone.utc)
            row = BodyMeasurement(
                user_id=uid,
                date=date(2026, 4, 13),
                source="renpho",
                measured_at=ts,
                weight_kg=80.5,
                body_fat_percent=18.2,
                muscle_mass_percent=42.1,
                bone_mass_kg=3.2,
                bmr_kcal=1750,
                visceral_fat=8.0,
                subcutaneous_fat_percent=14.5,
                protein_percent=19.3,
                body_age=28,
                cardiac_index=2.8,
                sport_flag=True,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            assert row.weight_kg == 80.5
            assert row.cardiac_index == 2.8
            assert row.sport_flag is True
            assert row.source == "renpho"

    async def test_two_measurements_same_day_different_time(self):
        """Two measurements on the same day with different measured_at should both be stored."""
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            d = date(2026, 4, 13)
            session.add(BodyMeasurement(
                user_id=uid, date=d, source="renpho",
                measured_at=datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc),
                weight_kg=80.5,
            ))
            session.add(BodyMeasurement(
                user_id=uid, date=d, source="renpho",
                measured_at=datetime(2026, 4, 13, 20, 0, tzinfo=timezone.utc),
                weight_kg=81.0,
            ))
            await session.commit()
            rows = (await session.execute(
                select(BodyMeasurement).where(
                    BodyMeasurement.user_id == uid,
                    BodyMeasurement.date == d,
                )
            )).scalars().all()
            assert len(rows) == 2

    async def test_unique_constraint_violation(self):
        """Same user + source + measured_at should raise IntegrityError."""
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            ts = datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc)
            session.add(BodyMeasurement(
                user_id=uid, date=date(2026, 4, 13), source="renpho",
                measured_at=ts, weight_kg=80.5,
            ))
            await session.commit()
            session.add(BodyMeasurement(
                user_id=uid, date=date(2026, 4, 13), source="renpho",
                measured_at=ts, weight_kg=81.0,
            ))
            with pytest.raises(Exception):  # IntegrityError
                await session.commit()

    async def test_to_dict_filters_none_values(self):
        """Fitbit row with only weight/bmi/body_fat should NOT include Renpho-only fields."""
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            ts = datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc)
            row = BodyMeasurement(
                user_id=uid, date=date(2026, 4, 13), source="fitbit",
                measured_at=ts,
                weight_kg=80.5, bmi=24.3, body_fat_percent=18.2,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            d = row.to_dict()
            assert d["weight_kg"] == 80.5
            assert d["bmi"] == 24.3
            assert d["body_fat_percent"] == 18.2
            assert "muscle_mass_percent" not in d
            assert "cardiac_index" not in d
            assert "sport_flag" not in d
            assert "visceral_fat" not in d

    async def test_multi_source_same_time(self):
        """Fitbit + Renpho with the same measured_at but different source should both be stored."""
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            ts = datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc)
            session.add(BodyMeasurement(
                user_id=uid, date=date(2026, 4, 13), source="fitbit",
                measured_at=ts, weight_kg=80.5,
            ))
            session.add(BodyMeasurement(
                user_id=uid, date=date(2026, 4, 13), source="renpho",
                measured_at=ts, weight_kg=80.7, body_fat_percent=18.2,
            ))
            await session.commit()
            rows = (await session.execute(
                select(BodyMeasurement).where(BodyMeasurement.user_id == uid)
            )).scalars().all()
            assert len(rows) == 2
            sources = {r.source for r in rows}
            assert sources == {"fitbit", "renpho"}


# ─── Upsert function tests ─────────────────────────────────────────


@pytest.mark.asyncio
class TestUpsertBodyMeasurement:
    async def test_insert_new(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            ts = datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc)
            await upsert_body_measurement(
                session, uid, "renpho", ts,
                date=date(2026, 4, 13),
                weight_kg=80.5, body_fat_percent=18.2, muscle_mass_percent=42.1,
            )
            await session.commit()
            row = (await session.execute(
                select(BodyMeasurement).where(BodyMeasurement.user_id == uid)
            )).scalar_one()
            assert row.weight_kg == 80.5
            assert row.body_fat_percent == 18.2
            assert row.muscle_mass_percent == 42.1

    async def test_update_existing(self):
        async with test_session_maker() as session:
            uid = uuid.uuid4()
            ts = datetime(2026, 4, 13, 8, 0, tzinfo=timezone.utc)
            await upsert_body_measurement(
                session, uid, "renpho", ts,
                date=date(2026, 4, 13),
                weight_kg=80.5, body_fat_percent=18.2,
            )
            await session.commit()
            # Upsert again with updated values
            await upsert_body_measurement(
                session, uid, "renpho", ts,
                date=date(2026, 4, 13),
                weight_kg=81.0, body_fat_percent=17.9,
            )
            await session.commit()
            rows = (await session.execute(
                select(BodyMeasurement).where(BodyMeasurement.user_id == uid)
            )).scalars().all()
            assert len(rows) == 1
            assert rows[0].weight_kg == 81.0
            assert rows[0].body_fat_percent == 17.9
