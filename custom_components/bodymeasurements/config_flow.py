"""Config and options flow for the Body Measurements integration."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.util import slugify

from .const import (
    CONF_BIRTHDAY,
    CONF_BODY_FAT_METHOD,
    CONF_GENDER,
    CONF_HEIGHT,
    CONF_MEASUREMENT_SOURCES,
    CONF_SENSOR_WEIGHT,
    CONSTRAINT_HEIGHT_MAX,
    CONSTRAINT_HEIGHT_MIN,
    DEFAULT_BODY_FAT_METHOD,
    DOMAIN,
)
from .models import BodyFatMethod, Gender

_MEASUREMENT_DOMAINS = ["sensor", "input_number", "number"]


def _height_selector() -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            mode=selector.NumberSelectorMode.BOX,
            min=CONSTRAINT_HEIGHT_MIN,
            max=CONSTRAINT_HEIGHT_MAX,
            step=0.1,
            unit_of_measurement="cm",
        )
    )


def _entity_selector() -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain=_MEASUREMENT_DOMAINS)
    )


def _sources_fields(defaults: Any) -> dict:
    """Weight (required) + optional circumference source selectors."""
    fields: dict = {
        vol.Required(
            CONF_SENSOR_WEIGHT,
            description={"suggested_value": defaults.get(CONF_SENSOR_WEIGHT)},
        ): _entity_selector(),
    }
    for key in CONF_MEASUREMENT_SOURCES:
        fields[
            vol.Optional(key, description={"suggested_value": defaults.get(key)})
        ] = _entity_selector()
    return fields


@callback
def _user_schema(defaults: dict[str, Any] | MappingProxyType[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME)): str,
            vol.Required(
                CONF_BIRTHDAY,
                description={"suggested_value": defaults.get(CONF_BIRTHDAY)},
            ): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.DATE)
            ),
            vol.Required(CONF_GENDER, default=defaults.get(CONF_GENDER)): vol.In(
                {gender: gender.value for gender in Gender}
            ),
            vol.Required(
                CONF_HEIGHT,
                description={"suggested_value": defaults.get(CONF_HEIGHT)},
            ): _height_selector(),
            vol.Optional(
                CONF_BODY_FAT_METHOD,
                default=defaults.get(CONF_BODY_FAT_METHOD, DEFAULT_BODY_FAT_METHOD),
            ): vol.In({method: method.value for method in BodyFatMethod}),
            **_sources_fields(defaults),
        }
    )


@callback
def _options_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_HEIGHT,
                description={"suggested_value": defaults.get(CONF_HEIGHT)},
            ): _height_selector(),
            vol.Optional(
                CONF_BODY_FAT_METHOD,
                default=defaults.get(CONF_BODY_FAT_METHOD, DEFAULT_BODY_FAT_METHOD),
            ): vol.In({method: method.value for method in BodyFatMethod}),
            **_sources_fields(defaults),
        }
    )


def _validate(user_input: dict[str, Any], errors: dict[str, str]) -> None:
    height = user_input.get(CONF_HEIGHT)
    if height is None or not (
        CONSTRAINT_HEIGHT_MIN <= float(height) <= CONSTRAINT_HEIGHT_MAX
    ):
        errors[CONF_HEIGHT] = "height_invalid"


class BodyMeasurementsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial configuration."""

    VERSION = 1

    def __init__(self) -> None:
        super().__init__()
        self._data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> BodyMeasurementsOptionsFlow:
        """Return the options flow."""
        return BodyMeasurementsOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the single-step user config."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                cv.date(user_input[CONF_BIRTHDAY])
            except vol.Invalid:
                errors[CONF_BIRTHDAY] = "invalid_date"

            _validate(user_input, errors)

            name_slug = slugify(user_input[CONF_NAME].strip())
            if not name_slug:
                errors[CONF_NAME] = "name_invalid"

            if not errors:
                await self.async_set_unique_id(name_slug)
                self._abort_if_unique_id_configured()
                self._data = {**user_input, CONF_NAME: user_input[CONF_NAME].strip()}
                return self.async_create_entry(
                    title=self._data[CONF_NAME],
                    data=self._data,
                    options=self._data,
                )

        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=_user_schema(user_input or self._data),
        )


class BodyMeasurementsOptionsFlow(OptionsFlow):
    """Handle reconfiguration of height + source entities."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry
        self._data = dict(config_entry.data) | dict(config_entry.options)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the options step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            _validate(user_input, errors)
            if not errors:
                # Preserve identity keys, overwrite the editable ones.
                self._data.update(user_input)
                return self.async_create_entry(data=self._data)

        return self.async_show_form(
            step_id="init",
            errors=errors,
            data_schema=_options_schema(user_input or self._data),
        )
