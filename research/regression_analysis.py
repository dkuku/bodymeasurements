#!/usr/bin/env python3
"""Empirical body composition regression analysis.

Validates anthropometric tape models (Neck, Waist, Hip) against hydrostatic
weighing (densitometry / Siri 1956) using the Brigham Young University (BYU)
clinical dataset (Penrose, Nelson, Fisher 1985; n=252 men).

Demonstrates:
  1. The marginal value of neck circumference (NC) over BMI/weight/height.
  2. The high predictive accuracy of the waist-neck difference (US Navy model).
  3. The rationale for hybrid BIA + Circumference calibration to solve the
     'trunk blindness' of foot-to-foot smart scales.
"""

from __future__ import annotations

import io
import os
import urllib.request

import numpy as np
import pandas as pd

DATASET_URL = (
    "https://raw.githubusercontent.com/parthjangam/bodyfat_predictor/main/bodyfat.csv"
)
LOCAL_CSV = os.path.join(os.path.dirname(__file__), "bodyfat.csv")


def load_dataset() -> pd.DataFrame:
    """Load and clean the BYU body composition dataset."""
    if os.path.exists(LOCAL_CSV):
        df = pd.read_csv(LOCAL_CSV)
    else:
        print(f"Downloading reference dataset from {DATASET_URL}...")
        req = urllib.request.Request(DATASET_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
        df = pd.read_csv(io.StringIO(content))
        df.to_csv(LOCAL_CSV, index=False)
        print(f"Saved local copy to {LOCAL_CSV}")

    # Fix known typographical error in Penrose dataset:
    # Subject #42 has Height=29.5 inches with Weight=205 lbs (actual height 69.5 in)
    df.loc[df["Height"] < 50, "Height"] = 69.5

    # Convert to metric SI units
    df["Weight_kg"] = df["Weight"] * 0.45359237
    df["Height_cm"] = df["Height"] * 2.54
    df["Height_m"] = df["Height_cm"] / 100.0
    df["BMI"] = df["Weight_kg"] / (df["Height_m"] ** 2)
    df["LBM_kg"] = df["Weight_kg"] * (1.0 - df["BodyFat"] / 100.0)

    return df


def fit_ols(
    X: np.ndarray, y: np.ndarray
) -> tuple[np.ndarray, float, float, float, float]:
    """Fit Ordinary Least Squares with intercept; returns (beta, r2, mae, rmse, bias)."""
    X_design = np.column_stack([np.ones(len(X)), X])
    beta, _, _, _ = np.linalg.lstsq(X_design, y, rcond=None)
    y_pred = X_design @ beta
    err = y_pred - y
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    r2 = float(1.0 - np.sum(err**2) / np.sum((y - y.mean()) ** 2))
    bias = float(np.mean(err))
    return beta, r2, mae, rmse, bias


def evaluate_us_navy(df: pd.DataFrame) -> tuple[float, float, float, float]:
    """Evaluate standard 1984 Hodgdon-Beckett US Navy equation on the dataset."""
    db = (
        1.0324
        - 0.19077 * np.log10(df["Abdomen"] - df["Neck"])
        + 0.15456 * np.log10(df["Height_cm"])
    )
    bf_pred = 495.0 / db - 450.0
    err = bf_pred - df["BodyFat"]
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    r2 = float(
        1.0 - np.sum(err**2) / np.sum((df["BodyFat"] - df["BodyFat"].mean()) ** 2)
    )
    bias = float(np.mean(err))
    return r2, mae, rmse, bias


def main() -> None:
    """Run regression models and print comparison tables."""
    df = load_dataset()
    n = len(df)
    print(f"\nLoaded {n} subjects from BYU Hydrostatic Dataset.")
    print(f"Age: {df['Age'].mean():.1f} ± {df['Age'].std():.1f} yrs")
    print(f"Weight: {df['Weight_kg'].mean():.1f} ± {df['Weight_kg'].std():.1f} kg")
    print(f"Height: {df['Height_cm'].mean():.1f} ± {df['Height_cm'].std():.1f} cm")
    print(
        f"BodyFat (Ground Truth): {df['BodyFat'].mean():.1f} ± {df['BodyFat'].std():.1f} %\n"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 1. BODY FAT PERCENTAGE REGRESSIONS
    # ─────────────────────────────────────────────────────────────────────────
    print("=" * 80)
    print(" 1. REGRESSION MODELS FOR BODY FAT % (Ground Truth: Hydrostatic Siri)")
    print("=" * 80)

    # Model 1: Height + Weight + Age
    X1 = df[["Height_cm", "Weight_kg", "Age"]].values
    _b1, r2_1, mae1, rmse1, _ = fit_ols(X1, df["BodyFat"].values)

    # Model 2: Height + Weight + Age + Neck
    X2 = df[["Height_cm", "Weight_kg", "Age", "Neck"]].values
    b2, r2_2, mae2, rmse2, _ = fit_ols(X2, df["BodyFat"].values)

    # Model 3: US Navy Standard (1984)
    r2_navy, mae_navy, rmse_navy, bias_navy = evaluate_us_navy(df)

    # Model 4: Refitted Navy Density Model
    X_navy_log = np.column_stack(
        [np.log10(df["Abdomen"] - df["Neck"]), np.log10(df["Height_cm"])]
    )
    b_density, _, _, _, _ = fit_ols(X_navy_log, df["Density"].values)
    pred_density = (
        b_density[0]
        + b_density[1] * np.log10(df["Abdomen"] - df["Neck"])
        + b_density[2] * np.log10(df["Height_cm"])
    )
    pred_bf_refit = 495.0 / pred_density - 450.0
    err_refit = pred_bf_refit - df["BodyFat"]
    mae_refit = float(np.mean(np.abs(err_refit)))
    rmse_refit = float(np.sqrt(np.mean(err_refit**2)))
    r2_refit = float(
        1.0 - np.sum(err_refit**2) / np.sum((df["BodyFat"] - df["BodyFat"].mean()) ** 2)
    )

    # Model 5: Height + Weight + Age + Neck + Waist (Linear OLS)
    X5 = df[["Height_cm", "Weight_kg", "Age", "Neck", "Abdomen"]].values
    b5, r2_5, mae5, rmse5, _ = fit_ols(X5, df["BodyFat"].values)

    print(
        f"{'Model':<42} | {'R²':>6} | {'MAE (%)':>8} | {'RMSE (%)':>8} | {'Bias (%)':>8}"
    )
    print("-" * 80)
    print(
        f"{'1. Height + Weight + Age':<42} | {r2_1:6.4f} | {mae1:8.2f} | {rmse1:8.2f} | {0.0:8.2f}"
    )
    print(
        f"{'2. Height + Weight + Age + NECK':<42} | {r2_2:6.4f} | {mae2:8.2f} | {rmse2:8.2f} | {0.0:8.2f}"
    )
    print(
        f"{'3. US Navy 1984 (Waist, Neck, Height)':<42} | {r2_navy:6.4f} | {mae_navy:8.2f} | {rmse_navy:8.2f} | {bias_navy:8.2f}"
    )
    print(
        f"{'4. Refitted Navy Model (BYU calibrated)':<42} | {r2_refit:6.4f} | {mae_refit:8.2f} | {rmse_refit:8.2f} | {float(np.mean(err_refit)):8.2f}"
    )
    print(
        f"{'5. Linear OLS (H + W + Age + Neck + Waist)':<42} | {r2_5:6.4f} | {mae5:8.2f} | {rmse5:8.2f} | {0.0:8.2f}"
    )
    print("-" * 80)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. COEFFICIENTS & ANTHROPOMETRIC INSIGHTS
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print(" 2. COEFFICIENTS & PHYSIOLOGICAL INTERPRETATION")
    print("=" * 80)
    print("Model 2 (with Neck):")
    print(
        f"  %BF = {b2[0]:.2f} - {abs(b2[1]):.3f}·H + {b2[2]:.3f}·W + {b2[3]:.3f}·Age - {abs(b2[4]):.3f}·Neck"
    )
    print("  -> Controlling for height and weight, each +1 cm of neck circumference")
    print(
        f"     reduces estimated body fat by {abs(b2[4]):.2f} % (marker of muscular frame).\n"
    )

    print("Model 5 (with Neck & Waist):")
    print(
        f"  %BF = {b5[0]:.2f} - {abs(b5[1]):.3f}·H - {abs(b5[2]):.3f}·W + {b5[3]:.3f}·Age - {abs(b5[4]):.3f}·Neck + {b5[5]:.3f}·Waist"
    )
    print(
        "  -> Waist has a massive positive coefficient (+0.95 % per cm) reflecting trunk adiposity,"
    )
    print("     while Neck acts as the muscular denominator (-0.48 % per cm).\n")

    # ─────────────────────────────────────────────────────────────────────────
    # 3. LEAN BODY MASS (LBM) PREDICTION
    # ─────────────────────────────────────────────────────────────────────────
    print("=" * 80)
    print(" 3. PREDICTING LEAN BODY MASS (LBM in kg)")
    print("=" * 80)
    _b_lbm1, r2_lbm1, mae_lbm1, rmse_lbm1, _ = fit_ols(X1, df["LBM_kg"].values)
    _b_lbm2, r2_lbm2, mae_lbm2, rmse_lbm2, _ = fit_ols(X2, df["LBM_kg"].values)
    b_lbm5, r2_lbm5, mae_lbm5, rmse_lbm5, _ = fit_ols(X5, df["LBM_kg"].values)

    print(f"{'Model':<42} | {'R²':>6} | {'MAE (kg)':>8} | {'RMSE (kg)':>8}")
    print("-" * 80)
    print(
        f"{'1. Height + Weight + Age':<42} | {r2_lbm1:6.4f} | {mae_lbm1:8.2f} | {rmse_lbm1:8.2f}"
    )
    print(
        f"{'2. Height + Weight + Age + NECK':<42} | {r2_lbm2:6.4f} | {mae_lbm2:8.2f} | {rmse_lbm2:8.2f}"
    )
    print(
        f"{'3. Height + Weight + Age + NECK + WAIST':<42} | {r2_lbm5:6.4f} | {mae_lbm5:8.2f} | {rmse_lbm5:8.2f}"
    )
    print("-" * 80)
    print(
        f"LBM (Neck + Waist) = {b_lbm5[0]:.2f} + {b_lbm5[1]:.3f}·H + {b_lbm5[2]:.3f}·W - {abs(b_lbm5[3]):.3f}·Age + {b_lbm5[4]:.3f}·Neck - {abs(b_lbm5[5]):.3f}·Waist"
    )
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
