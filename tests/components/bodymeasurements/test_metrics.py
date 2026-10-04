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


def test_density_and_volume() -> None:
    """Body density and volume match physical principles (V = W / D)."""
    inp = _male()
    density = metrics.body_density(inp)
    volume = metrics.body_volume(inp)
    assert density == pytest.approx(1.062, abs=0.01)
    assert volume == pytest.approx(80.0 / density, abs=0.1)

    # Deurenberg fallback density when neck/waist tape is missing
    tape_missing = _male(waist=None, neck=None)
    fallback_d = metrics.body_density(tape_missing)
    assert fallback_d is not None
    assert 1.03 < fallback_d < 1.08


def test_bone_and_muscle_compartments() -> None:
    """Bone mass, soft muscle mass, and muscle-to-fat ratios match multi-compartment model."""
    inp = _male()
    bone = metrics.bone_mass(inp)
    assert bone == pytest.approx(3.38, abs=0.1)

    # Wrist frame adjustment test
    robust_frame = _male(wrist=19.8)  # 10% thicker wrist than reference 18.0 cm
    slender_frame = _male(wrist=16.2)  # 10% thinner wrist than reference 18.0 cm
    assert metrics.bone_mass(robust_frame) > bone
    assert metrics.bone_mass(slender_frame) < bone

    # Soft muscle mass = Weight - Fat Mass - Bone Mass
    muscle = metrics.muscle_mass(inp)
    fat = metrics.fat_mass(inp)
    assert muscle is not None and fat is not None
    assert muscle + fat + bone == pytest.approx(80.0, abs=0.1)

    # Muscle-to-fat and fat-to-muscle ratios
    mfr = metrics.muscle_to_fat_ratio(inp)
    fmr = metrics.fat_to_muscle_ratio(inp)
    assert mfr == pytest.approx(muscle / fat, abs=0.01)
    assert fmr == pytest.approx(fat / muscle, abs=0.01)
    assert mfr > 4.0  # Athletic/healthy male profile


def test_skeletal_muscle_mass_with_calf() -> None:
    """Santos et al. 2019 calf formula refines SMM when calf circumference is given."""
    base_male = _male()
    # Lee 2000 model without calf
    smm_lee = metrics.skeletal_muscle_mass(base_male)
    assert smm_lee == pytest.approx(33.43, abs=0.1)

    # Santos 2019 model with calf
    calf_male = _male(calf=38.0)
    smm_santos = metrics.skeletal_muscle_mass(calf_male)
    assert smm_santos is not None and 26.0 < smm_santos < 32.0


def test_primary_body_fat_precedence() -> None:
    """Estimator precedence: Navy tape → Deurenberg."""
    # 1. Full tape → Navy (≈16.11 %)
    navy_inp = _male()
    assert metrics.fat_mass(navy_inp) == pytest.approx(80 * 0.1611, abs=0.2)

    # 2. No neck/tape → Deurenberg (≈21.48 %)
    deurenberg_inp = _male(neck=None)
    assert metrics.fat_mass(deurenberg_inp) == pytest.approx(80 * 0.2148, abs=0.2)


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
    """Only weight configured → baseline metrics present, tape metrics absent."""
    minimal = Inputs(height=180.0, age=35, gender=Gender.MALE, weight=80.0)
    result = metrics.compute_all(minimal)

    for present in (
        Metric.BMI,
        Metric.PONDERAL_INDEX,
        Metric.BODY_DENSITY,
        Metric.BODY_VOLUME,
        Metric.BODY_FAT_DEURENBERG,
        Metric.SKELETAL_MUSCLE_MASS,
        Metric.SMI,
        Metric.FAT_MASS,
        Metric.LEAN_BODY_MASS,
        Metric.BONE_MASS,
        Metric.MUSCLE_MASS,
        Metric.MUSCLE_TO_FAT_RATIO,
        Metric.FAT_TO_MUSCLE_RATIO,
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


def test_compute_all_with_full_measurements() -> None:
    """Full measurements compute all 23 derived metrics."""
    full = Inputs(
        height=180.0,
        age=35,
        gender=Gender.MALE,
        weight=80.0,
        waist=85.0,
        hip=95.0,
        neck=38.0,
        calf=38.0,
        wrist=18.0,
    )
    result = metrics.compute_all(full)
    assert len(result) == len(metrics.CALCULATORS)
    assert Metric.BODY_FAT_NAVY in result
    assert Metric.BODY_VOLUME in result
    assert Metric.BONE_MASS in result
    assert Metric.MUSCLE_MASS in result
    assert Metric.MUSCLE_TO_FAT_RATIO in result


def test_compute_all_without_weight_is_empty() -> None:
    """No weight means nothing can be computed."""
    assert metrics.compute_all(Inputs(height=180.0, age=35, gender=Gender.MALE)) == {}
