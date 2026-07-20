"""Unit tests for the pure metric calculations."""

from __future__ import annotations

import pytest

from custom_components.bodymeasurements import metrics
from custom_components.bodymeasurements.models import Gender, Inputs, Metric


def _male(**overrides) -> Inputs:
    """Return a reference male profile, overriding any fields given."""
    base: dict = {
        "height": 180.0,
        "age": 35,
        "gender": Gender.MALE,
        "weight": 80.0,
        "waist": 85.0,
        "hip": 95.0,
        "neck": 38.0,
    }
    base.update(overrides)
    return Inputs(**base)


# ── Shape indices ──────────────────────────────────────────────────────────


def test_bmi_and_ratios() -> None:
    """BMI, WHtR, WHR and the ponderal index match hand-computed values."""
    inp = _male()
    assert metrics.bmi(inp) == pytest.approx(24.69, abs=0.05)
    assert metrics.whtr(inp) == pytest.approx(0.472, abs=0.005)
    assert metrics.whr(inp) == pytest.approx(0.895, abs=0.005)
    assert metrics.ponderal_index(inp) == pytest.approx(13.72, abs=0.05)


def test_bri_absi_conicity_bai() -> None:
    """The shape indices match hand-computed values."""
    inp = _male()
    assert metrics.bri(inp) == pytest.approx(2.85, abs=0.1)
    assert metrics.absi(inp) == pytest.approx(0.0747, abs=0.001)
    assert metrics.conicity_index(inp) == pytest.approx(1.170, abs=0.01)
    assert metrics.bai(inp) == pytest.approx(21.33, abs=0.1)


# ── Body-fat estimators ────────────────────────────────────────────────────


def test_body_fat_navy_male() -> None:
    """The US Navy tape method matches the reference calculation."""
    assert metrics.body_fat_navy(_male()) == pytest.approx(16.11, abs=0.1)


def test_body_fat_deurenberg_and_rfm() -> None:
    """Deurenberg and RFM estimators match hand-computed values."""
    inp = _male()
    assert metrics.body_fat_deurenberg(inp) == pytest.approx(21.48, abs=0.1)
    assert metrics.relative_fat_mass(inp) == pytest.approx(21.65, abs=0.1)


def test_navy_female_requires_hip() -> None:
    """The female Navy formula needs hip; without it the result is None."""
    female = _male(gender=Gender.FEMALE, hip=None)
    assert metrics.body_fat_navy(female) is None
    assert metrics.body_fat_navy(_male(gender=Gender.FEMALE)) is not None


def test_primary_body_fat_prefers_navy() -> None:
    """Masses use the Navy estimate when available, else Deurenberg."""
    inp = _male()
    # Navy is available, so masses use it (≈16.1 %), not Deurenberg (≈21.5 %).
    assert metrics.fat_mass(inp) == pytest.approx(80 * 0.1611, abs=0.2)
    # Without neck, Navy is unavailable → falls back to Deurenberg.
    no_neck = _male(neck=None)
    assert metrics.fat_mass(no_neck) == pytest.approx(80 * 0.2148, abs=0.2)


# ── Masses & indices ───────────────────────────────────────────────────────


def test_masses_and_indices() -> None:
    """Lean mass, FFMI, FMI, SMM and SMI match hand-computed values."""
    inp = _male()
    assert metrics.lean_body_mass(inp) == pytest.approx(67.1, abs=0.3)
    assert metrics.ffmi(inp) == pytest.approx(20.7, abs=0.1)
    assert metrics.fmi(inp) == pytest.approx(3.98, abs=0.1)
    assert metrics.skeletal_muscle_mass(inp) == pytest.approx(33.43, abs=0.1)
    assert metrics.smi(inp) == pytest.approx(10.32, abs=0.05)


def test_normalized_ffmi() -> None:
    """Normalised FFMI equals raw at 1.8 m and adjusts otherwise."""
    assert metrics.normalized_ffmi(20.0, 180.0) == 20.0
    assert metrics.normalized_ffmi(20.0, 170.0) > 20.0
    assert metrics.normalized_ffmi(0.0, 180.0) is None


# ── Gating: metrics skipped when inputs are missing ────────────────────────


def test_compute_all_gates_on_missing_measurements() -> None:
    """Only weight configured → BMI-family present, tape metrics absent."""
    minimal = Inputs(height=180.0, age=35, gender=Gender.MALE, weight=80.0)
    result = metrics.compute_all(minimal)

    for present in (
        Metric.BMI,
        Metric.PONDERAL_INDEX,
        Metric.BODY_FAT_DEURENBERG,
        Metric.SKELETAL_MUSCLE_MASS,
        Metric.SMI,
        Metric.FAT_MASS,
        Metric.LEAN_BODY_MASS,
        Metric.FFMI,
        Metric.FMI,
    ):
        assert present in result

    for absent in (
        Metric.WHTR,
        Metric.WHR,
        Metric.BRI,
        Metric.ABSI,
        Metric.CONICITY_INDEX,
        Metric.BAI,
        Metric.BODY_FAT_NAVY,
        Metric.RFM,
    ):
        assert absent not in result


def test_compute_all_without_weight_is_empty() -> None:
    """No weight means nothing can be computed."""
    assert metrics.compute_all(Inputs(height=180.0, age=35, gender=Gender.MALE)) == {}
