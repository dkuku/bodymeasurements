# Example Configurations for Body Measurements

This folder provides ready-to-use configurations to quickly set up tape measurement helpers and an interactive body silhouette dashboard card in **Home Assistant**.

---

## 📁 Included Files

1. **`input_numbers.yaml`**:
   Full set of `input_number` helper entities for every supported body measurement:
   - Neck (`body_neck`)
   - Chest (`body_chest`)
   - Biceps (`body_biceps`)
   - Waist (`body_waist`)
   - Hip (`body_hip`)
   - Wrist (`body_wrist`)
   - Thigh (`body_thigh`)
   - Calf (`body_calf`)
   - Ankle (`body_ankle`)
   - Weight (`body_weight`, optional if not using a smart scale)

2. **`lovelace_silhouette_card.yaml`**:
   Interactive Lovelace `picture-elements` card using the built-in body silhouette graphic.
   - Click on any measurement pill directly on the human body diagram to update that circumference in centimeters.
   - Automatically loads the silhouette graphic bundled with the integration from `/bodymeasurements_static/body_silhouette.jpg`.

---

## 🚀 Quick Setup Guide

### Step 1: Add Input Number Helpers

Add the helpers to your `configuration.yaml`:

```yaml
input_number: !include example_config/input_numbers.yaml
```

*(Alternatively, create the helpers via the Home Assistant UI in **Settings** → **Devices & Services** → **Helpers**).*

Restart Home Assistant to apply.

### Step 2: Configure Body Measurements Profile

1. Navigate to **Settings** → **Devices & Services** → **Body Measurements**.
2. Create or edit your profile.
3. Select your weight entity (e.g. from your smart scale or `input_number.body_weight`).
4. Select the corresponding `input_number.body_*` entities for your tape circumferences.

### Step 3: Add the Dashboard Card

1. Open your Home Assistant Dashboard.
2. Click **Edit Dashboard** → **Add Card** → choose **Manual**.
3. Copy and paste the contents of `lovelace_silhouette_card.yaml`.
4. Save and start tracking your body composition on the fly!
