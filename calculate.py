#!/usr/bin/env python3
"""Interactive & CLI tool for testing Body Measurements calculations."""

from __future__ import annotations

import argparse

from custom_components.bodymeasurements import metrics
from custom_components.bodymeasurements.models import (
    BodyFatMethod,
    Gender,
    Inputs,
    Metric,
)


def _prompt_float(prompt: str, default: float | None = None) -> float | None:
    def_str = f" [{default}]" if default is not None else ""
    val = input(f"{prompt}{def_str}: ").strip()
    if not val:
        return default
    try:
        return float(val)
    except ValueError:
        print("Nieprawidłowa liczba, pomijam.")
        return default


def main() -> None:
    """Run anthropometric body composition calculation."""
    parser = argparse.ArgumentParser(
        description="Oblicz objętość ciała, masę mięśni, kości i tłuszczu z obwodów."
    )
    parser.add_argument("--height", type=float, help="Wzrost w cm (np. 180)")
    parser.add_argument("--weight", type=float, help="Waga w kg (np. 80.5)")
    parser.add_argument("--age", type=int, help="Wiek w latach (np. 35)")
    parser.add_argument(
        "--gender",
        choices=["male", "female", "m", "k"],
        help="Płeć: male / female (lub m / k)",
    )
    parser.add_argument("--waist", type=float, help="Obwód talii / pasa w cm")
    parser.add_argument("--neck", type=float, help="Obwód szyi / karku w cm")
    parser.add_argument(
        "--hip", type=float, help="Obwód bioder w cm (wymagany dla kobiet)"
    )
    parser.add_argument("--calf", type=float, help="Obwód łydki w cm (opcjonalny)")
    parser.add_argument(
        "--wrist", type=float, help="Obwód nadgarstka w cm (opcjonalny)"
    )
    parser.add_argument(
        "--method",
        choices=["calibrated", "navy", "deurenberg"],
        default="calibrated",
        help="Główny model tłuszczowy: calibrated / navy / deurenberg (domyślnie calibrated)",
    )

    args = parser.parse_args()

    # Jeśli nie podano argumentów, zapytaj interaktywnie
    if args.height is None and args.weight is None:
        print("=" * 60)
        print("  KALKULATOR ANTROPOMETRYCZNY (BODY MEASUREMENTS v0.3.0)")
        print("  Podaj swoje pomiary (wartości w nawiasach zatwierdzasz Enterem)")
        print("=" * 60)

        height = _prompt_float("Wzrost [cm]", 180.0) or 180.0
        weight = _prompt_float("Waga [kg]", 80.0) or 80.0
        age = int(_prompt_float("Wiek [lata]", 35.0) or 35)
        g_raw = input("Płeć (m - mężczyzna / k - kobieta) [m]: ").strip().lower()
        gender = (
            Gender.FEMALE if g_raw in ("k", "female", "f", "kobieta") else Gender.MALE
        )

        print("\n--- Pomiary taśmą (kluczowe do gęstości, tłuszczu i mięśni) ---")
        waist = _prompt_float("Obwód talii / pasa na wysokości pępka [cm]")
        neck = _prompt_float("Obwód szyi / karku tuż pod krtanią [cm]")
        hip = None
        if (
            gender == Gender.FEMALE
            or input("Chcesz podać obwód bioder? (t/n) [n]: ").strip().lower() == "t"
        ):
            hip = _prompt_float("Obwód bioder w najszerszym miejscu [cm]")

        print("\n--- Pomiary opcjonalne (poprawka na kości i precyzja mięśni) ---")
        wrist = _prompt_float(
            "Obwód nadgarstka w najwęższym miejscu [cm] (poprawka na kości)"
        )
        calf = _prompt_float("Obwód łydki w najszerszym miejscu [cm] (precyzja mięśni)")

        print("\n--- Wybór modelu tkanki tłuszczowej ---")
        print("  1) Model skalibrowany klinicznie z wagą (BYU OLS) [ZALECANY]")
        print("  2) Klasyczny model US Navy 1984 (taśma bez wagi)")
        print("  3) Deurenberg (z wagi i BMI)")
        m_raw = input("Wybór modelu [1]: ").strip()
        if m_raw == "2":
            method = BodyFatMethod.NAVY
        elif m_raw == "3":
            method = BodyFatMethod.DEURENBERG
        else:
            method = BodyFatMethod.CALIBRATED
    else:
        height = args.height or 180.0
        weight = args.weight or 80.0
        age = args.age or 35
        gender = Gender.FEMALE if args.gender in ("female", "k", "f") else Gender.MALE
        waist = args.waist
        neck = args.neck
        hip = args.hip
        calf = args.calf
        wrist = args.wrist
        method = BodyFatMethod(args.method)

    inp = Inputs(
        height=height,
        weight=weight,
        age=age,
        gender=gender,
        waist=waist,
        neck=neck,
        hip=hip,
        calf=calf,
        wrist=wrist,
        body_fat_method=method,
    )

    res = metrics.compute_all(inp)

    print("\n" + "=" * 60)
    print("                WYNIKI ANALIZY CIAŁA")
    print("=" * 60)

    print("\n[1] FIZYKA & DENSYTOMETRIA")
    if Metric.BODY_DENSITY in res:
        print(f"  • Gęstość ciała:          {res[Metric.BODY_DENSITY]:.3f} g/cm³")
    if Metric.BODY_VOLUME in res:
        print(f"  • Całkowita objętość:     {res[Metric.BODY_VOLUME]:.1f} litrów (dm³)")

    print("\n[2] PORÓWNANIE MODELI TKANKI TŁUSZCZOWEJ (% BF)")
    if Metric.BODY_FAT_CALIBRATED in res:
        is_sel = " [AKTYWNY]" if method == BodyFatMethod.CALIBRATED else ""
        print(
            f"  • Model skalibrowany (z wagą, BYU): {res[Metric.BODY_FAT_CALIBRATED]:.1f} %{is_sel}"
        )
    if Metric.BODY_FAT_NAVY in res:
        is_sel = " [AKTYWNY]" if method == BodyFatMethod.NAVY else ""
        print(
            f"  • Model US Navy (1984, bez wagi):   {res[Metric.BODY_FAT_NAVY]:.1f} %{is_sel}"
        )
    if Metric.BODY_FAT_DEURENBERG in res:
        is_sel = " [AKTYWNY]" if method == BodyFatMethod.DEURENBERG else ""
        print(
            f"  • Model Deurenberg (z BMI):         {res[Metric.BODY_FAT_DEURENBERG]:.1f} %{is_sel}"
        )
    if Metric.RFM in res:
        print(f"  • Względna masa tłuszczu (RFM):     {res[Metric.RFM]:.1f} %")

    print("\n[3] ROZBICIE KOMPONENTÓW TKANKOWYCH (wg wybranego modelu)")
    if Metric.FAT_MASS in res:
        print(f"  • Masa tłuszczu:          {res[Metric.FAT_MASS]:.1f} kg")
    if Metric.LEAN_BODY_MASS in res:
        print(f"  • Masa beztłuszczowa:     {res[Metric.LEAN_BODY_MASS]:.1f} kg (LBM)")
    if Metric.BONE_MASS in res:
        frame_info = " (skorygowana o nadgarstek)" if wrist else " (model standardowy)"
        print(f"  • Masa mineralna kości:   {res[Metric.BONE_MASS]:.2f} kg{frame_info}")
    if Metric.MUSCLE_MASS in res:
        print(
            f"  • Czysta masa mięśniowa:  {res[Metric.MUSCLE_MASS]:.1f} kg (Waga - Tłuszcz - Kości)"
        )
    if Metric.SKELETAL_MUSCLE_MASS in res:
        smm_info = " (model Santos DEXA z łydki)" if calf else " (model Lee MRI)"
        print(
            f"  • Mięśnie szkieletowe:    {res[Metric.SKELETAL_MUSCLE_MASS]:.1f} kg{smm_info}"
        )

    print("\n[4] BIOMARKERY METABOLICZNE & REKOMPOZYCJA")
    if Metric.MUSCLE_TO_FAT_RATIO in res:
        mfr = res[Metric.MUSCLE_TO_FAT_RATIO]
        status = (
            "Doskonały (atletyczny)"
            if mfr >= 4.0
            else ("Prawidłowy" if mfr >= 2.5 else "Niski (ryzyko otłuszczenia)")
        )
        print(f"  • Stosunek mięśni/tłuszcz: {mfr:.2f}  [{status}]")
    if Metric.FAT_TO_MUSCLE_RATIO in res:
        print(f"  • Stosunek tłuszcz/mięśnie: {res[Metric.FAT_TO_MUSCLE_RATIO]:.2f}")
    if Metric.FFMI in res:
        norm_ffmi = metrics.normalized_ffmi(res[Metric.FFMI], height)
        print(
            f"  • Wskaźnik FFMI:          {res[Metric.FFMI]:.1f} kg/m² (znormalizowany: {norm_ffmi})"
        )

    print("\n[5] WSKAŹNIKI KSZTAŁTU CIAŁA")
    print(f"  • BMI:                    {res.get(Metric.BMI, 0):.1f} kg/m²")
    if Metric.WHTR in res:
        whtr = res[Metric.WHTR]
        whtr_eval = (
            "w normie (< 0.5)"
            if whtr <= 0.5
            else "podwyższone ryzyko sercowo-naczyniowe"
        )
        print(f"  • Talia / Wzrost (WHtR):  {whtr:.2f}  [{whtr_eval}]")
    if Metric.BRI in res:
        print(f"  • Krągłość ciała (BRI):   {res[Metric.BRI]:.2f}")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
