# Body Measurements & Hybrid BIA

Derive clinical body-composition metrics from **tape measurements** and optionally combine them with smart scale **Bioelectrical Impedance Analysis (BIA)** to overcome the "trunk blindness" of foot-to-foot smart scales.

The official measurement companion to [**bodymiscale**](https://github.com/dkuku/bodymiscale): point a profile at your weight and impedance entities plus a few circumferences (waist, hip, neck) and get anthropometric indices, calibrated hybrid body-fat, and muscle-mass estimates as sensors.

## Highlights

- **Hybrid BIA + Tape Estimator:** Anchors body fat to real visceral and subcutaneous trunk dimensions, eliminating the blind spots of smart scale foot sensors.
- **Works with any source entity:** Use `sensor`, `number`, or `input_number` entities.
- **Progressive Unlocking:** Only **weight** is required — every extra circumference or impedance entity unlocks more metrics.
- **Automatic Hierarchy:** Masses and indices automatically use the most accurate available body fat method:
  $$\text{Hybrid (Tape + BIA)} \longrightarrow \text{US Navy (Tape)} \longrightarrow \text{BIA Scale} \longrightarrow \text{Deurenberg (BMI)}$$
- **Automatic Recalculation:** Recomputes automatically whenever any source value changes.

## Metrics Overview

| Required Inputs | Metrics |
| :--- | :--- |
| **Weight only** | BMI, Ponderal index, Deurenberg body fat, Lee-2000 skeletal muscle mass, SMI, Fat mass, Lean body mass, FFMI, FMI |
| **+ Waist** | Waist-to-height ratio (WHtR), Body Roundness Index (BRI), A Body Shape Index (ABSI), Conicity index, Relative Fat Mass (RFM) |
| **+ Waist & Hip** | Waist-to-hip ratio (WHR) |
| **+ Hip** | Body Adiposity Index (BAI) |
| **+ Neck & Waist (+ Hip for ♀)** | Body fat (US Navy / Army tape method) |
| **+ Impedance** | Body fat (Hardware BIA) |
| **+ Impedance & Tape** | **Body fat (Hybrid BIA + Tape Calibration)** |

## Setup

1. Install via HACS, then **restart Home Assistant**.
2. **Settings → Devices & Services → Add Integration → Body Measurements**.
3. Enter name, birthday, gender, and height; select your **weight** entity and, optionally, waist / hip / neck / impedance entities.
