"""Tests for the measurement handler wiring (source entities → metrics)."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from custom_components.bodymeasurements.const import (
    CONF_BIRTHDAY,
    CONF_GENDER,
    CONF_HEIGHT,
    CONF_SENSOR_HIP,
    CONF_SENSOR_NECK,
    CONF_SENSOR_WAIST,
    CONF_SENSOR_WEIGHT,
)
from custom_components.bodymeasurements.handler import MeasurementsHandler
from custom_components.bodymeasurements.models import Gender, Metric


def _config(**sources: str) -> dict[str, Any]:
    return {
        "name": "Tester",
        CONF_BIRTHDAY: "1990-03-10",
        CONF_GENDER: Gender.MALE.value,
        CONF_HEIGHT: 180.0,
        **sources,
    }


async def test_weight_only_computes_baseline_metrics(hass: HomeAssistant) -> None:
    """With only weight, BMI-family metrics are produced; tape ones are not."""
    handler = MeasurementsHandler(
        hass, _config(**{CONF_SENSOR_WEIGHT: "sensor.weight"}), "e1"
    )

    bmi: list[float] = []
    whtr: list[float] = []
    handler.subscribe(Metric.BMI, bmi.append)
    handler.subscribe(Metric.WHTR, whtr.append)

    hass.states.async_set("sensor.weight", "80.0")
    await hass.async_block_till_done()

    assert bmi and bmi[-1] == 80.0 / 1.8**2
    assert not whtr  # no waist configured
    handler.unload()


async def test_full_measurements_flow(hass: HomeAssistant) -> None:
    """All configured circumferences unlock the tape-based metrics."""
    handler = MeasurementsHandler(
        hass,
        _config(
            **{
                CONF_SENSOR_WEIGHT: "sensor.weight",
                CONF_SENSOR_WAIST: "sensor.waist",
                CONF_SENSOR_HIP: "sensor.hip",
                CONF_SENSOR_NECK: "sensor.neck",
            }
        ),
        "e2",
    )

    assert handler.configured_sources == frozenset(
        {Metric.WEIGHT, Metric.WAIST, Metric.HIP, Metric.NECK}
    )

    navy: list[float] = []
    whr: list[float] = []
    handler.subscribe(Metric.BODY_FAT_NAVY, navy.append)
    handler.subscribe(Metric.WHR, whr.append)

    hass.states.async_set("sensor.weight", "80.0")
    hass.states.async_set("sensor.waist", "85.0")
    hass.states.async_set("sensor.hip", "95.0")
    hass.states.async_set("sensor.neck", "38.0")
    await hass.async_block_till_done()

    assert navy and 14 < navy[-1] < 18
    assert whr and whr[-1] == 85.0 / 95.0
    handler.unload()


async def test_volumetric_and_compartment_flow(hass: HomeAssistant) -> None:
    """Configuring circumferences unlocks volumetric and compartment sensors."""
    handler = MeasurementsHandler(
        hass,
        _config(
            **{
                CONF_SENSOR_WEIGHT: "sensor.weight",
                CONF_SENSOR_WAIST: "sensor.waist",
                CONF_SENSOR_NECK: "sensor.neck",
            }
        ),
        "e_volumetric",
    )

    density: list[float] = []
    volume: list[float] = []
    bone: list[float] = []
    muscle: list[float] = []
    mfr: list[float] = []

    handler.subscribe(Metric.BODY_DENSITY, density.append)
    handler.subscribe(Metric.BODY_VOLUME, volume.append)
    handler.subscribe(Metric.BONE_MASS, bone.append)
    handler.subscribe(Metric.MUSCLE_MASS, muscle.append)
    handler.subscribe(Metric.MUSCLE_TO_FAT_RATIO, mfr.append)

    hass.states.async_set("sensor.weight", "80.0")
    hass.states.async_set("sensor.waist", "85.0")
    hass.states.async_set("sensor.neck", "38.0")
    await hass.async_block_till_done()

    assert density and 1.04 < density[-1] < 1.08
    assert volume and 74.0 < volume[-1] < 77.0
    assert bone and 2.5 < bone[-1] < 4.0
    assert muscle and 60.0 < muscle[-1] < 66.0
    assert mfr and 4.0 < mfr[-1] < 6.0
    handler.unload()


async def test_unavailable_source_is_ignored(hass: HomeAssistant) -> None:
    """Non-numeric / unavailable source states must not crash or publish."""
    handler = MeasurementsHandler(
        hass,
        _config(
            **{CONF_SENSOR_WEIGHT: "sensor.weight", CONF_SENSOR_WAIST: "sensor.waist"}
        ),
        "e3",
    )

    whtr: list[float] = []
    handler.subscribe(Metric.WHTR, whtr.append)

    hass.states.async_set("sensor.weight", "80.0")
    hass.states.async_set("sensor.waist", "unavailable")
    await hass.async_block_till_done()
    assert not whtr

    hass.states.async_set("sensor.waist", "85.0")
    await hass.async_block_till_done()
    assert whtr and whtr[-1] == 85.0 / 180.0
    handler.unload()
