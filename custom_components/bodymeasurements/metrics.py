"""Pure, impedance-free body-composition calculations.

Every metric here is derived from tape measurements + basic profile data
(height, weight, age, gender) — no bio-impedance scale required. Functions are
pure: they take an :class:`Inputs` and return a ``float`` or ``None`` when the
required measurements are unavailable.

References
---------
- BMI / Ponderal index          : standard anthropometry
- Waist-to-height ratio (WHtR)   : Ashwell & Hsieh 2005 (cutoff 0.5)
- Waist-to-hip ratio (WHR)       : WHO 2008
- Body Roundness Index (BRI)     : Thomas et al. 2013
- A Body Shape Index (ABSI)      : Krakauer & Krakauer 2012
- Conicity index                 : Valdez 1991
- Body Adiposity Index (BAI)     : Bergman et al. 2011
- Body density & Navy body fat   : Hodgdon & Beckett 1984 (US Navy / US Army tape test)
- Siri equation                  : Siri 1956
- Body fat, BMI method           : Deurenberg et al. 1991
- Relative Fat Mass (RFM)        : Woolcott & Bergman 2018
- Body volume                    : V = Weight / Body Density
- Bone mass                      : multi-compartment bone mineral model with frame adjustment
- Muscle mass                    : Soft lean tissue mass (Weight - Fat Mass - Bone Mass)
- Muscle-to-fat ratio (MFR)      : Sarcopenia & recomposition biomarker
- Skeletal muscle mass           : Santos et al. 2019 (calf DEXA model) / Lee et al. 2000
- FFMI / FMI / SMI               : height-normalised compartment indices
"""

from __future__ import annotations

import math

from .models import Gender, Inputs, Metric
from .util import clamp

# Body-fat percentage bounds shared by every estimator.
_FAT_MIN, _FAT_MAX = 3.0, 75.0


def _male(inp: Inputs) -> bool:
    return inp.gender == Gender.MALE


# ─────────────────────────────────────────────────────────────────────────────
# BMI & shape indices
# ─────────────────────────────────────────────────────────────────────────────


def bmi(inp: Inputs) -> float | None:
    """Body Mass Index (kg/m²)."""
    if not inp.weight or inp.height_m <= 0:
        return None
    return clamp(inp.weight / inp.height_m**2, 5, 90)


def ponderal_index(inp: Inputs) -> float | None:
    """Ponderal (Rohrer) Index (kg/m³) — more height-robust than BMI."""
    if not inp.weight or inp.height_m <= 0:
        return None
    return inp.weight / inp.height_m**3


def whtr(inp: Inputs) -> float | None:
    """Waist-to-Height Ratio (health cutoff ≈ 0.5)."""
    if not inp.waist or inp.height <= 0:
        return None
    return inp.waist / inp.height


def whr(inp: Inputs) -> float | None:
    """Waist-to-Hip Ratio."""
    if not inp.waist or not inp.hip:
        return None
    return inp.waist / inp.hip


def bri(inp: Inputs) -> float | None:
    """Body Roundness Index (Thomas et al. 2013)."""
    if not inp.waist or inp.height_m <= 0:
        return None
    waist_m = inp.waist / 100.0
    # semi-minor / semi-major axis ratio of the modelled ellipse
    ratio = (waist_m / (2 * math.pi)) / (0.5 * inp.height_m)
    if ratio >= 1:
        return None
    eccentricity = math.sqrt(1 - ratio**2)
    return 364.2 - 365.5 * eccentricity


def absi(inp: Inputs) -> float | None:
    """Return A Body Shape Index (Krakauer 2012) — waist in m, height in m."""
    body_mass_index = bmi(inp)
    if body_mass_index is None or not inp.waist or inp.height_m <= 0:
        return None
    waist_m = inp.waist / 100.0
    return waist_m / (body_mass_index ** (2 / 3) * inp.height_m**0.5)


def conicity_index(inp: Inputs) -> float | None:
    """Conicity index (Valdez 1991)."""
    if not inp.waist or not inp.weight or inp.height_m <= 0:
        return None
    waist_m = inp.waist / 100.0
    return waist_m / (0.109 * math.sqrt(inp.weight / inp.height_m))


def bai(inp: Inputs) -> float | None:
    """Body Adiposity Index (Bergman 2011) — estimates body fat % from hip."""
    if not inp.hip or inp.height_m <= 0:
        return None
    return clamp(inp.hip / inp.height_m**1.5 - 18, _FAT_MIN, _FAT_MAX)


# ─────────────────────────────────────────────────────────────────────────────
# Density, volume & body-fat estimators
# ─────────────────────────────────────────────────────────────────────────────


def body_density(inp: Inputs) -> float | None:
    """Body density (g/cm³ or kg/L).

    Calculated via Hodgdon & Beckett (US Navy) density formula when waist and neck
    (and hip for females) are available; falls back to Siri-inverse from Deurenberg body fat.
    """
    if inp.neck and inp.waist and inp.height > 0:
        if _male(inp):
            diff = inp.waist - inp.neck
            if diff > 0:
                d = (
                    1.0324
                    - 0.19077 * math.log10(diff)
                    + 0.15456 * math.log10(inp.height)
                )
                return clamp(d, 0.90, 1.15)
        elif inp.hip:
            diff = inp.waist + inp.hip - inp.neck
            if diff > 0:
                d = (
                    1.29579
                    - 0.35004 * math.log10(diff)
                    + 0.22100 * math.log10(inp.height)
                )
                return clamp(d, 0.90, 1.15)

    # Fallback: inverse Siri equation from Deurenberg body fat
    fat_pct = body_fat_deurenberg(inp)
    if fat_pct is not None:
        return clamp(495.0 / (fat_pct + 450.0), 0.90, 1.15)

    return None


def body_volume(inp: Inputs) -> float | None:
    """Total body volume (liters / dm³) from weight and body density: V = W / D."""
    if not inp.weight:
        return None
    d = body_density(inp)
    if d is None or d <= 0:
        return None
    return inp.weight / d


def body_fat_navy(inp: Inputs) -> float | None:
    """Body fat % via the US Navy / US Army circumference (tape) method.

    Male   : requires neck + waist + height.
    Female : additionally requires hip.
    """
    if not inp.neck or not inp.waist or inp.height <= 0:
        return None

    if _male(inp):
        diff = inp.waist - inp.neck
        if diff <= 0:
            return None
        density = 1.0324 - 0.19077 * math.log10(diff) + 0.15456 * math.log10(inp.height)
    else:
        if not inp.hip:
            return None
        diff = inp.waist + inp.hip - inp.neck
        if diff <= 0:
            return None
        density = (
            1.29579 - 0.35004 * math.log10(diff) + 0.22100 * math.log10(inp.height)
        )

    if density <= 0:
        return None
    return clamp(495 / density - 450, _FAT_MIN, _FAT_MAX)


def body_fat_deurenberg(inp: Inputs) -> float | None:
    """Body fat % from BMI, age and sex (Deurenberg 1991) — needs no tape."""
    body_mass_index = bmi(inp)
    if body_mass_index is None:
        return None
    sex = 1 if _male(inp) else 0
    fat = 1.20 * body_mass_index + 0.23 * inp.age - 10.8 * sex - 5.4
    return clamp(fat, _FAT_MIN, _FAT_MAX)


def relative_fat_mass(inp: Inputs) -> float | None:
    """Relative Fat Mass (Woolcott & Bergman 2018) from waist + height."""
    if not inp.waist or inp.height <= 0:
        return None
    sex_female = 0 if _male(inp) else 1
    return clamp(
        64 - 20 * (inp.height / inp.waist) + 12 * sex_female, _FAT_MIN, _FAT_MAX
    )


def _primary_body_fat(inp: Inputs) -> float | None:
    """Best available body-fat estimate: Navy tape → Deurenberg."""
    navy = body_fat_navy(inp)
    if navy is not None:
        return navy
    return body_fat_deurenberg(inp)


# ─────────────────────────────────────────────────────────────────────────────
# Derived masses & compartment fractionation
# ─────────────────────────────────────────────────────────────────────────────


def fat_mass(inp: Inputs) -> float | None:
    """Fat mass (kg) from the primary body-fat estimate."""
    fat_pct = _primary_body_fat(inp)
    if fat_pct is None or not inp.weight:
        return None
    return inp.weight * fat_pct / 100.0


def lean_body_mass(inp: Inputs) -> float | None:
    """Lean body mass (kg) = weight − fat mass."""
    fat = fat_mass(inp)
    if fat is None or not inp.weight:
        return None
    return inp.weight - fat


def bone_mass(inp: Inputs) -> float | None:
    """Estimated bone mineral mass (kg) adjusted for skeletal frame.

    Baseline bone mineral content is derived from fat-free mass (FFM)
    using the validated clinical densitometry equation (Heymsfield / Tanita).
    When wrist circumference is provided, a frame adjustment factor
    (Metropolitan Life / Grant skeletal frame index) refines the bone mass
    for robust vs. delicate bone structures.
    """
    lbm = lean_body_mass(inp)
    if lbm is None:
        return None

    base_offset = 0.18016894 if _male(inp) else 0.245691014
    bmc = lbm * 0.05158 - base_offset
    bmc += 0.1 if bmc > 2.2 else -0.1

    # Frame adjustment if wrist circumference is measured
    if inp.wrist and inp.height > 0:
        ref_wrist = inp.height / (10.0 if _male(inp) else 10.5)
        frame_ratio = clamp(inp.wrist / ref_wrist, 0.8, 1.3)
        bmc *= frame_ratio

    return clamp(bmc, 0.5, 8.0)


def muscle_mass(inp: Inputs) -> float | None:
    """Total muscle / soft lean tissue mass (kg) = Weight - Fat Mass - Bone Mass."""
    if not inp.weight:
        return None
    fat = fat_mass(inp)
    bones = bone_mass(inp)
    if fat is None or bones is None:
        return None
    return max(0.0, inp.weight - fat - bones)


def muscle_to_fat_ratio(inp: Inputs) -> float | None:
    """Muscle-to-Fat Ratio (MFR) = Muscle Mass (kg) / Fat Mass (kg).

    Higher values indicate greater muscularity and lower adiposity.
    Standard metabolic biomarker for body recomposition and sarcopenic risk.
    """
    muscle = muscle_mass(inp)
    fat = fat_mass(inp)
    if muscle is None or fat is None or fat <= 0:
        return None
    return clamp(muscle / fat, 0.1, 50.0)


def fat_to_muscle_ratio(inp: Inputs) -> float | None:
    """Fat-to-Muscle Ratio (FMR) = Fat Mass (kg) / Muscle Mass (kg).

    Lower values indicate a leaner, more muscular physique.
    """
    muscle = muscle_mass(inp)
    fat = fat_mass(inp)
    if muscle is None or fat is None or muscle <= 0:
        return None
    return clamp(fat / muscle, 0.01, 10.0)


def skeletal_muscle_mass(inp: Inputs) -> float | None:
    """Skeletal muscle mass (kg).

    Uses Santos et al. 2019 (NHANES DEXA appendicular model) when calf circumference
    is available; otherwise uses Lee et al. 2000 MRI-validated anthropometric model.
    """
    if inp.height_m <= 0:
        return None

    sex = 1 if _male(inp) else 0

    if inp.calf and inp.calf > 0:
        asm = -10.427 + 0.768 * inp.calf - 0.029 * inp.age + 7.523 * sex
        smm = 1.17 * asm - 1.01
        return max(0.0, smm)

    if not inp.weight:
        return None
    smm = 0.244 * inp.weight + 7.80 * inp.height_m - 0.098 * inp.age + 6.6 * sex - 3.3
    return max(0.0, smm)


# ─────────────────────────────────────────────────────────────────────────────
# Height-normalised indices & proportions
# ─────────────────────────────────────────────────────────────────────────────


def ffmi(inp: Inputs) -> float | None:
    """Fat-Free Mass Index (kg/m²) = LBM / height²."""
    lbm = lean_body_mass(inp)
    if lbm is None or inp.height_m <= 0:
        return None
    return lbm / inp.height_m**2


def fmi(inp: Inputs) -> float | None:
    """Fat Mass Index (kg/m²) = fat mass / height²."""
    fat = fat_mass(inp)
    if fat is None or inp.height_m <= 0:
        return None
    return fat / inp.height_m**2


def smi(inp: Inputs) -> float | None:
    """Skeletal Muscle Index (kg/m²) = SMM / height² — sarcopenia screening."""
    smm = skeletal_muscle_mass(inp)
    if smm is None or inp.height_m <= 0:
        return None
    return smm / inp.height_m**2


def normalized_ffmi(ffmi_value: float, height_cm: float) -> float | None:
    """Height-normalised FFMI (adjusted to a 1.8 m reference)."""
    if ffmi_value <= 0 or height_cm <= 0:
        return None
    return round(ffmi_value + 6.3 * (1.8 - height_cm / 100.0), 1)


# ─────────────────────────────────────────────────────────────────────────────
# Aggregation
# ─────────────────────────────────────────────────────────────────────────────

# Metric → calculation function. Order is display/compute order.
CALCULATORS: dict[Metric, object] = {
    Metric.BMI: bmi,
    Metric.PONDERAL_INDEX: ponderal_index,
    Metric.WHTR: whtr,
    Metric.WHR: whr,
    Metric.BRI: bri,
    Metric.ABSI: absi,
    Metric.CONICITY_INDEX: conicity_index,
    Metric.BAI: bai,
    Metric.BODY_DENSITY: body_density,
    Metric.BODY_VOLUME: body_volume,
    Metric.BODY_FAT_NAVY: body_fat_navy,
    Metric.BODY_FAT_DEURENBERG: body_fat_deurenberg,
    Metric.RFM: relative_fat_mass,
    Metric.FAT_MASS: fat_mass,
    Metric.LEAN_BODY_MASS: lean_body_mass,
    Metric.BONE_MASS: bone_mass,
    Metric.MUSCLE_MASS: muscle_mass,
    Metric.MUSCLE_TO_FAT_RATIO: muscle_to_fat_ratio,
    Metric.FAT_TO_MUSCLE_RATIO: fat_to_muscle_ratio,
    Metric.FFMI: ffmi,
    Metric.FMI: fmi,
    Metric.SKELETAL_MUSCLE_MASS: skeletal_muscle_mass,
    Metric.SMI: smi,
}


def compute_all(inp: Inputs) -> dict[Metric, float]:
    """Compute every derived metric that has enough data; skip the rest."""
    result: dict[Metric, float] = {}
    for metric, func in CALCULATORS.items():
        value = func(inp)  # type: ignore[operator]
        if value is not None:
            result[metric] = value
    return result
