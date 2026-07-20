# Body Measurements

A Home Assistant custom integration that derives body-composition metrics from
**tape measurements** — no bio-impedance scale required. It is the measurement
companion to [bodymiscale](https://github.com/dckiller51/bodymiscale): where
bodymiscale turns a smart scale's weight + impedance into metrics, this
integration turns a weight entity plus a few circumferences (waist, hip, neck)
into anthropometric indices and body-fat / muscle estimates.

## How it works

You point a profile at existing Home Assistant entities that hold your
measurements — typically `input_number` helpers you update after measuring, or
`sensor`/`number` entities from another source. Only **weight** is required;
every additional circumference unlocks more metrics. The integration recomputes
whenever a source entity changes and exposes one sensor per metric.

## Metrics

| Metric | Needs (besides height/weight/age/sex) | Reference |
|---|---|---|
| BMI, Ponderal index | — | standard |
| Body fat (Deurenberg) | — | Deurenberg 1991 |
| Skeletal muscle mass, SMI | — | Lee 2000 (anthropometric) |
| Fat mass, Lean body mass, FFMI, FMI | — | derived from body fat |
| Waist-to-height ratio | waist | Ashwell 2005 |
| Body roundness index (BRI) | waist | Thomas 2013 |
| A body shape index (ABSI) | waist | Krakauer 2012 |
| Conicity index | waist | Valdez 1991 |
| Relative fat mass (RFM) | waist | Woolcott 2018 |
| Waist-to-hip ratio | waist + hip | WHO 2008 |
| Body adiposity index (BAI) | hip | Bergman 2011 |
| Body fat (Navy/Army tape) | neck + waist (+ hip for women) | Hodgdon & Beckett 1984 |

Fat mass / lean mass / FFMI / FMI use the most accurate available body-fat
estimate: the Navy circumference method when the required tapes are configured,
otherwise the BMI-based Deurenberg estimate.

## Installation

Copy `custom_components/bodymeasurements` into your Home Assistant `config`
directory (or add this repo to HACS as a custom repository), restart, then add
**Body Measurements** from *Settings → Devices & Services → Add Integration*.

## Development

```bash
pip install -e ".[dev]"
python3 -m pytest
```

## Status

Early scaffold (v0.1.0). The calculation core and per-metric sensors work and
are unit-tested. Planned next: a circumference-based Lee muscle model (arm /
thigh / calf girths), more body-fat methods, and translations beyond English.
