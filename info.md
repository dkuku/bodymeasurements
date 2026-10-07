# Body Measurements & Anthropometric Body Composition

Derive clinical body-composition metrics, volume, density, and tissue compartments purely from **tape measurements and weight** — no flawed bioimpedance scales required.

The official measurement companion to [**bodymiscale**](https://github.com/dkuku/bodymiscale): point a profile at your weight and tape measurements (waist, hip, neck, calf, wrist) and get complete physical volume, body density, bone mass correction, muscle-to-fat ratios, and shape indices as Home Assistant sensors.

## Highlights

- **Pure Physical Model:** Relies on tape circumferences and weight, completely bypassing the hydration artifacts and trunk blindness of foot-to-foot bioimpedance.
- **Physical Volume & Density:** Computes total body volume ($V = W / D_b$ in liters) and body density ($D_b$ in g/cm³) from validated densitometric models.
- **Tissue Fractionation:** Accurately separates body mass into Fat Mass, Lean Body Mass, Bone Mineral Mass (with skeletal frame correction), and Soft Muscle Mass.
- **Metabolic Biomarkers:** Computes **Muscle-to-Fat Ratio (MFR)** and **Fat-to-Muscle Ratio (FMR)** for body recomposition and sarcopenia screening.
- **Works with any source entity:** Use `sensor`, `number`, or `input_number` entities.
- **Progressive Unlocking:** Only **weight** is required — every extra circumference unlocks more precise sensors.
- **Automatic Recalculation:** Recomputes automatically whenever any source entity changes.

## Metrics Overview

| Required Inputs | Metrics |
| :--- | :--- |
| **Weight only** | BMI, Ponderal index, Body density (Deurenberg fallback), Body volume ($V = W/D$), Deurenberg body fat, Fat mass, Lean body mass, Bone mass, Soft muscle mass, Muscle-to-Fat ratio (MFR), Fat-to-Muscle ratio (FMR), Skeletal muscle mass (Lee 2000), SMI, FFMI, FMI |
| **+ Waist** | Waist-to-height ratio (WHtR), Body Roundness Index (BRI), A Body Shape Index (ABSI), Conicity index, Relative Fat Mass (RFM) |
| **+ Waist & Hip** | Waist-to-hip ratio (WHR) |
| **+ Hip** | Body Adiposity Index (BAI) |
| **+ Neck & Waist (+ Hip for ♀)** | Body density (Hodgdon & Beckett), Body fat (US Navy tape method), High-precision volume |
| **+ Calf (optional)** | Refined Skeletal Muscle Mass (Santos et al. 2019 NHANES DEXA model) |
| **+ Wrist (optional)** | Skeletal frame adjustment factor for Bone Mass |

## Setup

1. Install via HACS, then **restart Home Assistant**.
2. **Settings → Devices & Services → Add Integration → Body Measurements**.
3. Enter name, birthday, gender, and height; select your **weight** entity and, optionally, waist / hip / neck / calf / wrist / etc.
4. Add the interactive body silhouette card to your dashboard using the templates in [`example_config/`](example_config/).
