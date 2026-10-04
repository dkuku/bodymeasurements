# Body Measurements & Hybrid BIA

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/dkuku/bodymeasurements)](https://github.com/dkuku/bodymeasurements/releases)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-16%20passed-brightgreen.svg)](tests/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A comprehensive body-composition and anthropometry platform for **Home Assistant** and **Python**. It derives clinical anthropometric indices, shape metrics, and body fat from **tape measurements** (waist, hip, neck) and optionally combines them with smart scale **Bioelectrical Impedance Analysis (BIA)** to solve the infamous **"trunk blindness"** of consumer smart scales.

It is designed both as a standalone measurement tool and as the official companion to smart scale integrations such as [**bodymiscale**](https://github.com/dkuku/bodymiscale).

---

## 🔬 The Problem: "Trunk Blindness" of Smart Scales

Consumer smart scales (Xiaomi Mi Scale 2 / S400, Withings Body, Eufy, Renpho) measure foot-to-foot impedance:
1. **Physics ($R = \rho \cdot L / A$):** Long and slender legs account for **over 70%** of total measured electrical resistance, while the thick trunk accounts for **less than 15%**.
2. **The Flaw:** Most human adipose tissue (subcutaneous and deep visceral fat) is stored in the **trunk**. A foot-to-foot scale is largely blind to abdominal fat changes and easily fooled by leg musculature or transient hydration swings.
3. **The Solution:** By anchoring body composition to physical circumference measurements (**Neck, Waist, Hip**), the **Hybrid Estimator** eliminates this geometric blind spot while keeping the convenience of daily automated weigh-ins.

> 📖 **Read the full scientific whitepaper & clinical validation:**  
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

## 🧮 Available Metrics

Every metric is computed on the fly. Only **weight** is strictly required; every additional circumference or impedance entity unlocks more metrics:

| Metric | Required Inputs | Reference / Clinical Standard |
| :--- | :--- | :--- |
| **Body Fat (Hybrid BIA + Tape)** | Weight, Waist, Neck, Impedance (+ Hip for ♀) | Inverse-variance weighted ensemble (0.65 Navy + 0.35 BIA) |
| **Body Fat (US Navy Tape)** | Weight, Waist, Neck (+ Hip for ♀) | Hodgdon & Beckett 1984 (US Navy / DoD) |
| **Body Fat (BIA)** | Weight, Height, Age, Gender, Impedance | Hardware-calibrated foot-to-foot BIA (Heymsfield 2005) |
| **Body Fat (Deurenberg)** | Weight, Height, Age, Gender (No tape required) | Deurenberg et al. 1991 (BMI-derived) |
| **Relative Fat Mass (RFM)** | Waist, Height | Woolcott & Bergman 2018 |
| **Body Adiposity Index (BAI)** | Hip, Height | Bergman et al. 2011 |
| **Lean Body Mass (LBM) & Fat Mass** | Weight + best available body fat | Siri 1956 two-compartment model |
| **Fat-Free Mass Index (FFMI & Norm FFMI)** | LBM, Height | VanItallie 1990 (normalized to 1.8 m reference) |
| **Fat Mass Index (FMI)** | Fat Mass, Height | Schutz et al. 2002 |
| **Skeletal Muscle Mass & SMI** | Weight, Height, Age, Gender | Lee et al. 2000 (anthropometric MRI model) |
| **Waist-to-Height Ratio (WHtR)** | Waist, Height | Ashwell & Hsieh 2005 (Cardiometabolic cutoff 0.5) |
| **Waist-to-Hip Ratio (WHR)** | Waist, Hip | WHO 2008 standard |
| **Body Roundness Index (BRI)** | Waist, Height | Thomas et al. 2013 |
| **A Body Shape Index (ABSI)** | Waist, Height, Weight | Krakauer & Krakauer 2012 |
| **Conicity Index** | Waist, Height, Weight | Valdez 1991 |
| **BMI & Ponderal (Rohrer) Index** | Weight, Height | Quetelet 1832 / Rohrer 1921 |

### 🏆 Automatic Estimator Hierarchy
For derived masses (Fat Mass, LBM, FFMI, FMI), the integration automatically selects the **most accurate available estimator**:
$$\text{Hybrid (Tape + BIA)} \longrightarrow \text{US Navy (Tape)} \longrightarrow \text{BIA Scale} \longrightarrow \text{Deurenberg (BMI)}$$

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
   * **Weight Entity:** Point to your smart scale weight sensor (e.g. `sensor.bodymiscale_user_weight`).
   * **Tape Entities (Optional):** Point to your `input_number` helpers or sensors for **Waist**, **Hip**, and **Neck**.
   * **Impedance Entity (Optional):** Point to your smart scale impedance sensor (e.g. `sensor.bodymiscale_user_impedance`).

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
    impedance=500.0,  # ohms from smart scale
)

# Compute all available metrics
results = metrics.compute_all(user)

print(f"Navy Tape Body Fat:   {results['body_fat_navy']:.1f} %")
print(f"BIA Scale Body Fat:   {results['body_fat_bia']:.1f} %")
print(f"Calibrated Hybrid:    {results['body_fat_hybrid']:.1f} %")
print(f"Lean Body Mass:       {results['lean_body_mass']:.1f} kg")
print(f"Body Roundness (BRI): {results['body_roundness_index']:.2f}")
```

---

## 🛠️ Development & Testing

```bash
git clone https://github.com/dkuku/bodymeasurements.git
cd bodymeasurements
pip install -e ".[dev]"

# Run full test suite
pytest

# Code style and formatting check
ruff check .
ruff format --check .
```

---

## 📄 License

Licensed under the **Apache License, Version 2.0**. See [LICENSE](LICENSE) for details.
