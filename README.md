# Body Measurements & Anthropometric Body Composition

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/dkuku/bodymeasurements)](https://github.com/dkuku/bodymeasurements/releases)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-18%20passed-brightgreen.svg)](tests/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A comprehensive body-composition and kinanthropometry platform for **Home Assistant** and **Python**. It derives physical body volume, densitometric body density, multi-compartment tissue masses (fat, soft muscle, bone), muscle-to-fat ratios, and shape indices purely from **tape measurements and weight** — completely eliminating reliance on flawed bioimpedance scales.

It is designed both as a standalone measurement tool and as the official companion to smart scale integrations such as [**bodymiscale**](https://github.com/dkuku/bodymiscale).

---

## 🔬 Why Anthropometry Over Bioimpedance (BIA)?

Consumer smart scales (Xiaomi Mi Scale 2 / S400, Withings Body, Eufy, Renpho) rely on foot-to-foot bioelectrical impedance:
1. **Physics ($R = \rho \cdot L / A$):** Long and slender legs account for **over 70%** of total measured resistance, while the thick trunk accounts for **less than 15%**.
2. **"Trunk Blindness":** Most human adipose tissue (subcutaneous and deep visceral fat) is concentrated in the **trunk**. Foot-to-foot scales are largely blind to abdominal fat changes and easily distorted by leg musculature.
3. **Hydration Artifacts:** BIA does not measure fat; it measures electrical conduction through total body water (TBW). A glass of water, sweating, pre-workout sodium, or glycogen fluctuations can skew body fat readings by 3–8% within hours.
4. **The Physical Alternative:** Physical tape circumferences (**Waist, Neck, Hip, Calf, Wrist**) directly measure anatomical boundaries and cross-sectional areas. Combined with total body weight, they allow precise calculation of:
   - **Body Density ($D_b$)** and **Volume ($V = W / D_b$)**
   - **Fat Mass** and **Lean Body Mass (FFM)**
   - **Bone Mass** (with skeletal frame correction)
   - **Soft Muscle Mass** ($W - \text{Fat Mass} - \text{Bone Mass}$)
   - **Muscle-to-Fat Ratio (MFR)**

> 📖 **Read the clinical research & regression analysis:**  
> [**Theoretical Foundation & Empirical Regression Analysis**](research/THEORY_AND_REGRESSION.md)  
> *Includes validation on the Brigham Young University (BYU) hydrostatic densitometry dataset ($n=252$).*

---

## 📊 Empirical Validation & Accuracy Benchmark

Evaluating estimators against **Hydrostatic Underwater Weighing (Densitometry / Siri 1956)** on the clinical BYU dataset:

| Method / Predictors | $R^2$ | Mean Absolute Error (MAE) | Root Mean Squared Error (RMSE) |
| :--- | :---: | :---: | :---: |
| **BMI / Height + Weight + Age** *(Standard scale without tape)* | 0.5545 | 4.48% | 5.57% |
| **Height + Weight + Age + Neck** | **0.5736** | **4.36%** | **5.45%** |
| **Standard US Navy Model 1984** *(Waist, Neck, Height)* | 0.6389 | 4.10% | 5.02% |
| **Calibrated US Navy Model** *(Refitted on BYU data)* | **0.7327** | **3.56%** | **4.32%** |
| **Calibrated Lean Body Mass (LBM)** *(Neck + Waist OLS)* | **0.8262** | **2.81 kg** | **3.43 kg** |

*Run the benchmark yourself:* `python3 research/regression_analysis.py`

---

## 🧮 Available Metrics (23 Sensors)

Every metric is computed on the fly. Only **weight** is strictly required; every additional circumference unlocks more high-precision sensors:

| Category | Metric | Required Inputs | Reference / Clinical Standard |
| :--- | :--- | :--- | :--- |
| **Densitometry & Volume** | **Body Density ($D_b$)** | Waist, Neck, Height (fallback: Deurenberg) | Hodgdon & Beckett 1984 / Siri 1956 ($\text{g/cm}^3$) |
| | **Body Volume ($V$)** | Weight, Density | $V = W / D_b$ ($\text{L}$ / $\text{dm}^3$) |
| **Body Fat** | **Body Fat (US Navy Tape)** | Weight, Waist, Neck (+ Hip for ♀) | Hodgdon & Beckett 1984 (US Navy / DoD standard) |
| | **Body Fat (Deurenberg)** | Weight, Height, Age, Gender | Deurenberg et al. 1991 (BMI-derived fallback) |
| | **Relative Fat Mass (RFM)** | Waist, Height | Woolcott & Bergman 2018 |
| | **Body Adiposity Index (BAI)** | Hip, Height | Bergman et al. 2011 |
| **Tissue Compartments** | **Fat Mass** | Weight + best available %BF | Two-compartment model ($\text{kg}$) |
| | **Lean Body Mass (LBM / FFM)** | Weight − Fat Mass | Two-compartment model ($\text{kg}$) |
| | **Bone Mass** | LBM (+ optional Wrist) | Heymsfield / Tanita BMC model with Grant frame adjustment ($\text{kg}$) |
| | **Soft Muscle Mass** | Weight − Fat Mass − Bone Mass | Multi-compartment tissue fractionation ($\text{kg}$) |
| | **Skeletal Muscle Mass (SMM)** | Weight, Height, Age, Sex (+ optional Calf) | Santos et al. 2019 (Calf DEXA) / Lee et al. 2000 (MRI) |
| **Ratios & Proportions** | **Muscle-to-Fat Ratio (MFR)** | Muscle Mass / Fat Mass | Body recomposition & sarcopenia biomarker |
| | **Fat-to-Muscle Ratio (FMR)** | Fat Mass / Muscle Mass | Adiposity-to-muscle load index |
| | **Fat-Free Mass Index (FFMI)** | LBM, Height | VanItallie 1990 (normalized to 1.8 m reference) |
| | **Fat Mass Index (FMI)** | Fat Mass, Height | Schutz et al. 2002 |
| | **Skeletal Muscle Index (SMI)** | SMM, Height | Sarcopenia screening index ($\text{kg/m}^2$) |
| **Shape & Anthropometry** | **Waist-to-Height Ratio (WHtR)** | Waist, Height | Ashwell & Hsieh 2005 (Cardiometabolic cutoff 0.5) |
| | **Waist-to-Hip Ratio (WHR)** | Waist, Hip | WHO 2008 standard |
| | **Body Roundness Index (BRI)** | Waist, Height | Thomas et al. 2013 |
| | **A Body Shape Index (ABSI)** | Waist, Height, Weight | Krakauer & Krakauer 2012 |
| | **Conicity Index** | Waist, Height, Weight | Valdez 1991 |
| | **BMI & Ponderal Index** | Weight, Height | Quetelet 1832 / Rohrer 1921 |

---

## 🚀 Installation & Setup in Home Assistant

### Option 1: Via HACS (Recommended)
1. In Home Assistant, open **HACS** $\rightarrow$ **Integrations** $\rightarrow$ Top right menu $\rightarrow$ **Custom repositories**.
2. Add `https://github.com/dkuku/bodymeasurements` with Category **Integration**.
3. Click **Download**, then restart Home Assistant.

### Option 2: Manual Installation
Copy `custom_components/bodymeasurements` into your Home Assistant `<config>/custom_components/` directory and restart.

---

## ⚙️ Configuration

1. In Home Assistant, navigate to **Settings** $\rightarrow$ **Devices & Services** $\rightarrow$ **Add Integration** $\rightarrow$ **Body Measurements**.
2. Enter your profile details:
   * **Name**, **Birthday**, **Gender**, **Height (cm)**.
   * **Weight Entity:** Point to your scale weight sensor (e.g. `sensor.bodymiscale_user_weight`).
   * **Tape Entities (Optional):** Point to your `input_number` helpers or sensors for:
     - **Waist**, **Hip**, **Neck** (core body fat & density)
     - **Calf** (high-precision skeletal muscle mass)
     - **Wrist** (skeletal frame bone correction)
     - **Thigh**, **Chest**, **Biceps**, **Ankle**

> 💡 **Tip:** Create `input_number` helpers in Home Assistant (e.g. `input_number.waist_circumference`) to easily update your tape measurements from your dashboard whenever you take new measurements.

---

## 💻 Standalone Python Usage

The pure metric calculation engine can be used independently without Home Assistant:

```python
from custom_components.bodymeasurements import metrics
from custom_components.bodymeasurements.models import Gender, Inputs

# Define user measurements
user = Inputs(
    height=180.0,  # cm
    age=35,
    gender=Gender.MALE,
    weight=80.0,  # kg
    waist=85.0,  # cm
    neck=38.0,  # cm
    calf=38.0,  # cm (optional)
    wrist=18.0,  # cm (optional)
)

# Compute all available metrics
results = metrics.compute_all(user)

print(f"Body Density:         {results['body_density']:.3f} g/cm³")
print(f"Total Body Volume:    {results['body_volume']:.1f} L")
print(f"Navy Tape Body Fat:   {results['body_fat_navy']:.1f} %")
print(f"Bone Mineral Mass:    {results['bone_mass']:.2f} kg")
print(f"Soft Muscle Mass:     {results['muscle_mass']:.1f} kg")
print(f"Muscle-to-Fat Ratio:  {results['muscle_to_fat_ratio']:.2f}")
print(f"Skeletal Muscle Mass: {results['skeletal_muscle_mass']:.1f} kg")
print(f"Body Roundness (BRI): {results['body_roundness_index']:.2f}")
```

---

## 🛠️ Development & Testing

```bash
git clone https://github.com/dkuku/bodymeasurements.git
cd bodymeasurements
pip install -e ".[dev]"

# Run full test suite (18 tests)
pytest

# Code style and formatting check
ruff check .
ruff format --check .
```

---

## 📄 License

Licensed under the **Apache License, Version 2.0**. See [LICENSE](LICENSE) for details.
