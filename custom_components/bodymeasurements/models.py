"""Models for the Body Measurements integration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .const import (
    CONF_SENSOR_HIP,
    CONF_SENSOR_NECK,
    CONF_SENSOR_WAIST,
    CONF_SENSOR_WEIGHT,
)


class Gender(StrEnum):
    """Gender enum."""

    MALE = "male"
    FEMALE = "female"


class Metric(StrEnum):
    """All metrics produced by the integration.

    The first block are raw *source* metrics (mirroring the configured source
    entities); the rest are *derived* indices computed from measurements.
    """

    # ── Source metrics (raw circumferences / weight) ───────────────────────
    WEIGHT = CONF_SENSOR_WEIGHT
    WAIST = CONF_SENSOR_WAIST
    HIP = CONF_SENSOR_HIP
    NECK = CONF_SENSOR_NECK

    # ── BMI & shape indices ────────────────────────────────────────────────
    BMI = "bmi"
    PONDERAL_INDEX = "ponderal_index"
    WHTR = "waist_to_height_ratio"
    WHR = "waist_to_hip_ratio"
    BRI = "body_roundness_index"
    ABSI = "a_body_shape_index"
    CONICITY_INDEX = "conicity_index"
    BAI = "body_adiposity_index"

    # ── Body-fat estimators ────────────────────────────────────────────────
    BODY_FAT_NAVY = "body_fat_navy"
    BODY_FAT_DEURENBERG = "body_fat_deurenberg"
    RFM = "relative_fat_mass"

    # ── Derived masses & height-normalised indices ─────────────────────────
    FAT_MASS = "fat_mass"
    LEAN_BODY_MASS = "lean_body_mass"
    FFMI = "fat_free_mass_index"
    FMI = "fat_mass_index"
    SKELETAL_MUSCLE_MASS = "skeletal_muscle_mass"
    SMI = "skeletal_muscle_index"


# Metrics that come directly from a configured source entity.
SOURCE_METRICS: frozenset[Metric] = frozenset(
    {Metric.WEIGHT, Metric.WAIST, Metric.HIP, Metric.NECK}
)


@dataclass(frozen=True)
class Inputs:
    """Everything the pure metric functions need for one recalculation.

    All lengths are centimetres, weight is kilograms. Optional fields are
    ``None`` when the corresponding source entity is not configured or has no
    valid value yet.
    """

    height: float
    age: int
    gender: Gender
    weight: float | None = None
    waist: float | None = None
    hip: float | None = None
    neck: float | None = None

    @property
    def height_m(self) -> float:
        """Height in metres."""
        return self.height / 100.0
