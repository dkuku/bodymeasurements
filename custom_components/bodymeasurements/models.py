"""Models for the Body Measurements integration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .const import (
    CONF_SENSOR_ANKLE,
    CONF_SENSOR_BICEPS,
    CONF_SENSOR_CALF,
    CONF_SENSOR_CHEST,
    CONF_SENSOR_HIP,
    CONF_SENSOR_NECK,
    CONF_SENSOR_THIGH,
    CONF_SENSOR_WAIST,
    CONF_SENSOR_WEIGHT,
    CONF_SENSOR_WRIST,
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
    CALF = CONF_SENSOR_CALF
    WRIST = CONF_SENSOR_WRIST
    THIGH = CONF_SENSOR_THIGH
    CHEST = CONF_SENSOR_CHEST
    BICEPS = CONF_SENSOR_BICEPS
    ANKLE = CONF_SENSOR_ANKLE

    # ── BMI & shape indices ────────────────────────────────────────────────
    BMI = "bmi"
    PONDERAL_INDEX = "ponderal_index"
    WHTR = "waist_to_height_ratio"
    WHR = "waist_to_hip_ratio"
    BRI = "body_roundness_index"
    ABSI = "a_body_shape_index"
    CONICITY_INDEX = "conicity_index"
    BAI = "body_adiposity_index"

    # ── Density, volume & body-fat estimators ──────────────────────────────
    BODY_DENSITY = "body_density"
    BODY_VOLUME = "body_volume"
    BODY_FAT_NAVY = "body_fat_navy"
    BODY_FAT_DEURENBERG = "body_fat_deurenberg"
    RFM = "relative_fat_mass"

    # ── Derived masses & compartment fractionation ─────────────────────────
    FAT_MASS = "fat_mass"
    LEAN_BODY_MASS = "lean_body_mass"
    BONE_MASS = "bone_mass"
    MUSCLE_MASS = "muscle_mass"
    SKELETAL_MUSCLE_MASS = "skeletal_muscle_mass"

    # ── Proportions, ratios & height-normalised indices ────────────────────
    MUSCLE_TO_FAT_RATIO = "muscle_to_fat_ratio"
    FAT_TO_MUSCLE_RATIO = "fat_to_muscle_ratio"
    FFMI = "fat_free_mass_index"
    FMI = "fat_mass_index"
    SMI = "skeletal_muscle_index"


# Metrics that come directly from a configured source entity.
SOURCE_METRICS: frozenset[Metric] = frozenset(
    {
        Metric.WEIGHT,
        Metric.WAIST,
        Metric.HIP,
        Metric.NECK,
        Metric.CALF,
        Metric.WRIST,
        Metric.THIGH,
        Metric.CHEST,
        Metric.BICEPS,
        Metric.ANKLE,
    }
)


@dataclass(frozen=True)
class Inputs:
    """Everything the pure metric functions need for one recalculation.

    All lengths are centimetres, weight is kilograms.
    Optional fields are ``None`` when the corresponding source entity is not
    configured or has no valid value yet.
    """

    height: float
    age: int
    gender: Gender
    weight: float | None = None
    waist: float | None = None
    hip: float | None = None
    neck: float | None = None
    calf: float | None = None
    wrist: float | None = None
    thigh: float | None = None
    chest: float | None = None
    biceps: float | None = None
    ankle: float | None = None

    @property
    def height_m(self) -> float:
        """Height in metres."""
        return self.height / 100.0
