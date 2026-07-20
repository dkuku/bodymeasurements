"""Base entity for the Body Measurements integration."""

from __future__ import annotations

from homeassistant.const import CONF_NAME
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription

from .const import DOMAIN, VERSION
from .handler import MeasurementsHandler


class BodyMeasurementsBaseEntity(Entity):
    """Base entity binding an entity to a profile handler + device."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        handler: MeasurementsHandler,
        entity_description: EntityDescription,
    ) -> None:
        super().__init__()
        self._handler = handler
        self.entity_description = entity_description

        name = handler.config[CONF_NAME]
        self._attr_unique_id = "_".join([DOMAIN, name, entity_description.key])
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            name=name,
            sw_version=VERSION,
            identifiers={(DOMAIN, handler.config_entry_id)},
        )
