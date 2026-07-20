# Body Measurements

Derive body-composition metrics from **tape measurements** — no bio-impedance
scale required. The measurement companion to
[bodymiscale](https://github.com/dckiller51/bodymiscale): point a profile at a
weight entity plus a few circumferences (waist, hip, neck) and get anthropometric
indices, body-fat and muscle-mass estimates as sensors.

## Highlights

- Works with any `sensor`, `number` or `input_number` entity as a source.
- Only **weight** is required — every extra circumference unlocks more metrics.
- Recomputes automatically whenever a source value changes.
- One sensor per metric, grouped under a single device per profile.

## Metrics

| Needs (besides height/weight/age/sex) | Metrics |
|---|---|
| nothing extra | BMI, Ponderal index, Deurenberg body-fat, Lee-2000 skeletal muscle mass, SMI, fat mass, lean body mass, FFMI, FMI |
| waist | Waist-to-height ratio, Body Roundness Index (BRI), A Body Shape Index (ABSI), Conicity index, Relative Fat Mass (RFM) |
| waist + hip | Waist-to-hip ratio |
| hip | Body Adiposity Index (BAI) |
| neck + waist (+ hip for women) | Body fat, US Navy/Army tape method |

Fat mass, lean mass, FFMI and FMI use the most accurate available body-fat
estimate: the Navy circumference method when its tapes are configured, otherwise
the BMI-based Deurenberg estimate.

## Setup

1. Install via HACS, then **restart Home Assistant**.
2. **Settings → Devices & Services → Add Integration → Body Measurements**.
3. Enter name, birthday, gender and height; pick your **weight** entity and,
   optionally, waist / hip / neck entities.

**Tip:** create `input_number` helpers for the circumferences you measure by
tape — they persist between updates and are the intended "store only
measurements" input.
