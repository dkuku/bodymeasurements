"""Sensor platform for the Body Measurements integration."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from typing import Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_GENDER, CONF_HEIGHT, DOMAIN, HANDLERS
from .entity import BodyMeasurementsBaseEntity
from .handler import MeasurementsHandler
from .metrics import normalized_ffmi
from .models import Gender, Metric

_LOGGER = logging.getLogger(__name__)

_UNIT_INDEX = "kg/m²"

# Optional attribute callback: (value, config) -> extra state attributes.
AttrFn = Callable[[float, Mapping[str, Any]], Mapping[str, Any]]


def _ffmi_attributes(value: float, config: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "normalized": normalized_ffmi(value, float(config.get(CONF_HEIGHT) or 0)),
    }


# (description, metric, required source metrics, attribute fn)
_SENSORS: tuple[
    tuple[SensorEntityDescription, Metric, tuple[Metric, ...], AttrFn | None], ...
] = (
    (
        SensorEntityDescription(
            key=Metric.BMI.value,
            translation_key="bmi",
            icon="mdi:human",
            native_unit_of_measurement=_UNIT_INDEX,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        Metric.BMI,
        (),
        None,
    ),
    (
        SensorEntityDescription(
            key=Metric.PONDERAL_INDEX.value,
            translation_key="ponderal_index",
            icon="mdi:human-male-height",
            native_unit_of_measurement="kg/m³",
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        Metric.PONDERAL_INDEX,
        (),
        None,
    ),
    (
        SensorEntityDescription(
            key=Metric.WHTR.value,
            translation_key="waist_to_height_ratio",
            icon="mdi:tape-measure",
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=2,
        ),
        Metric.WHTR,
        (Metric.WAIST,),
        None,
    ),
    (
        SensorEntityDescription(
            key=Metric.WHR.value,
            translation_key="waist_to_hip_ratio",
            icon="mdi:tape-measure",
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=2,
        ),
        Metric.WHR,
        (Metric.WAIST, Metric.HIP),
        None,
    ),
    (
        SensorEntityDescription(
            key=Metric.BRI.value,
            translation_key="body_roundness_index",
            icon="mdi:circle-outline",
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=2,
        ),
        Metric.BRI,
        (Metric.WAIST,),
        None,
    ),
    (
        SensorEntityDescription(
            key=Metric.ABSI.value,
            translation_key="a_body_shape_index",
            icon="mdi:human",
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=4,
        ),
        Metric.ABSI,
        (Metric.WAIST,),
        None,
    ),
    (
        SensorEntityDescription(
            key=Metric.CONICITY_INDEX.value,
            translation_key="conicity_index",
            icon="mdi:cone",
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=2,
        ),
        Metric.CONICITY_INDEX,
        (Metric.WAIST,),
        None,
    ),
    (
        SensorEntityDescription(
            key=Metric.BAI.value,
            translation_key="body_adiposity_index",
            icon="mdi:percent",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        Metric.BAI,
        (Metric.HIP,),
        None,
    ),
    (
        SensorEntityDescription(
            key=Metric.BODY_FAT_NAVY.value,
            translation_key="body_fat_navy",
            icon="mdi:percent",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        Metric.BODY_FAT_NAVY,
        (Metric.NECK, Metric.WAIST),
        None,
    ),
    (
        SensorEntityDescription(
            key=Metric.BODY_FAT_DEURENBERG.value,
            translation_key="body_fat_deurenberg",
            icon="mdi:percent",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        Metric.BODY_FAT_DEURENBERG,
        (),
        None,
    ),
    (
        SensorEntityDescription(
            key=Metric.RFM.value,
            translation_key="relative_fat_mass",
            icon="mdi:percent",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        Metric.RFM,
        (Metric.WAIST,),
        None,
    ),
    (
        SensorEntityDescription(
            key=Metric.FAT_MASS.value,
            translation_key="fat_mass",
            icon="mdi:scale-bathroom",
            native_unit_of_measurement=UnitOfMass.KILOGRAMS,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        Metric.FAT_MASS,
        (),
        None,
    ),
    (
        SensorEntityDescription(
            key=Metric.LEAN_BODY_MASS.value,
            translation_key="lean_body_mass",
            icon="mdi:arm-flex",
            native_unit_of_measurement=UnitOfMass.KILOGRAMS,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        Metric.LEAN_BODY_MASS,
        (),
        None,
    ),
    (
        SensorEntityDescription(
            key=Metric.FFMI.value,
            translation_key="fat_free_mass_index",
            icon="mdi:arm-flex",
            native_unit_of_measurement=_UNIT_INDEX,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        Metric.FFMI,
        (),
        _ffmi_attributes,
    ),
    (
        SensorEntityDescription(
            key=Metric.FMI.value,
            translation_key="fat_mass_index",
            icon="mdi:scale-bathroom",
            native_unit_of_measurement=_UNIT_INDEX,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        Metric.FMI,
        (),
        None,
    ),
    (
        SensorEntityDescription(
            key=Metric.SKELETAL_MUSCLE_MASS.value,
            translation_key="skeletal_muscle_mass",
            icon="mdi:arm-flex",
            native_unit_of_measurement=UnitOfMass.KILOGRAMS,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        Metric.SKELETAL_MUSCLE_MASS,
        (),
        None,
    ),
    (
        SensorEntityDescription(
            key=Metric.SMI.value,
            translation_key="skeletal_muscle_index",
            icon="mdi:arm-flex",
            native_unit_of_measurement=_UNIT_INDEX,
            state_class=SensorStateClass.MEASUREMENT,
            suggested_display_precision=1,
        ),
        Metric.SMI,
        (),
        None,
    ),
)


def _can_create(
    metric: Metric,
    required: tuple[Metric, ...],
    sources: frozenset[Metric],
    gender: Gender,
) -> bool:
    """Return True if every source needed for this sensor is configured."""
    if not all(src in sources for src in required):
        return False
    # US Navy method additionally needs hip for women.
    if metric is Metric.BODY_FAT_NAVY and gender == Gender.FEMALE:
        return Metric.HIP in sources
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for a config entry."""
    handler: MeasurementsHandler = hass.data[DOMAIN][HANDLERS][config_entry.entry_id]
    sources = handler.configured_sources
    gender = handler.config[CONF_GENDER]

    entities = [
        BodyMeasurementsSensor(handler, description, metric, attr_fn)
        for description, metric, required, attr_fn in _SENSORS
        if _can_create(metric, required, sources, gender)
    ]
    async_add_entities(entities)


class BodyMeasurementsSensor(BodyMeasurementsBaseEntity, RestoreSensor):
    """A single derived-metric sensor with cold-start restoration."""

    def __init__(
        self,
        handler: MeasurementsHandler,
        entity_description: SensorEntityDescription,
        metric: Metric,
        attr_fn: AttrFn | None,
    ) -> None:
        super().__init__(handler, entity_description)
        self._metric = metric
        self._attr_fn = attr_fn

    async def async_added_to_hass(self) -> None:
        """Restore the last value and subscribe to live updates."""
        await super().async_added_to_hass()

        last = await self.async_get_last_sensor_data()
        if last is not None and last.native_value is not None:
            self._attr_native_value = last.native_value
            self._apply_attributes(last.native_value)
            self.async_write_ha_state()

        def _on_value(value: float) -> None:
            precision = self.entity_description.suggested_display_precision
            self._attr_native_value = round(value, precision if precision else 2)
            self._apply_attributes(value)
            self.async_write_ha_state()

        self.async_on_remove(self._handler.subscribe(self._metric, _on_value))

    def _apply_attributes(self, value: Any) -> None:
        if self._attr_fn and isinstance(value, (int, float)):
            self._attr_extra_state_attributes = dict(
                self._attr_fn(float(value), self._handler.config)
            )
