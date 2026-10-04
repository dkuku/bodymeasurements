"""Measurement handler — reads source entities and publishes derived metrics."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from typing import Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    callback,
)
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_BIRTHDAY,
    CONF_GENDER,
    CONF_HEIGHT,
    CONF_SENSOR_ANKLE,
    CONF_SENSOR_BICEPS,
    CONF_SENSOR_CALF,
    CONF_SENSOR_CHEST,
    CONF_SENSOR_HIP,
    CONF_SENSOR_NECK,
    CONF_SENSOR_THIGH,
    CONF_SENSOR_WAIST,
    CONF_SENSOR_WEIGHT,
    CONF_SENSOR_WRIST,
)
from .metrics import compute_all
from .models import Gender, Inputs, Metric
from .util import get_age, to_float

_LOGGER = logging.getLogger(__name__)

# Maps a config key holding an entity_id to the raw source Metric it feeds.
_SOURCE_CONF_TO_METRIC: dict[str, Metric] = {
    CONF_SENSOR_WEIGHT: Metric.WEIGHT,
    CONF_SENSOR_WAIST: Metric.WAIST,
    CONF_SENSOR_HIP: Metric.HIP,
    CONF_SENSOR_NECK: Metric.NECK,
    CONF_SENSOR_CALF: Metric.CALF,
    CONF_SENSOR_WRIST: Metric.WRIST,
    CONF_SENSOR_THIGH: Metric.THIGH,
    CONF_SENSOR_CHEST: Metric.CHEST,
    CONF_SENSOR_BICEPS: Metric.BICEPS,
    CONF_SENSOR_ANKLE: Metric.ANKLE,
}


class MeasurementsHandler:
    """Owns one profile: subscribes to source entities, recomputes on change."""

    def __init__(
        self, hass: HomeAssistant, config: Mapping[str, Any], entry_id: str
    ) -> None:
        self._hass = hass
        self._entry_id = entry_id
        self._config: dict[str, Any] = {
            **config,
            CONF_GENDER: Gender(config[CONF_GENDER]),
        }
        self._name: str = config.get("name", entry_id)
        self._height = float(config[CONF_HEIGHT])
        self._age = get_age(config[CONF_BIRTHDAY])
        self._gender: Gender = self._config[CONF_GENDER]

        # entity_id → source Metric, and current raw values.
        self._entity_to_metric: dict[str, Metric] = {}
        for conf_key, metric in _SOURCE_CONF_TO_METRIC.items():
            entity_id = config.get(conf_key)
            if entity_id:
                self._entity_to_metric[entity_id] = metric

        self._sources: dict[Metric, float] = {}
        self._derived: dict[Metric, float] = {}
        self._subscribers: dict[Metric, list[Callable[[float], None]]] = {}
        self._remove_listener: CALLBACK_TYPE | None = None

        self._setup_listeners()

    # ── Properties ─────────────────────────────────────────────────────────

    @property
    def config(self) -> Mapping[str, Any]:
        """Return the (parsed) config."""
        return self._config

    @property
    def config_entry_id(self) -> str:
        """Return the config entry id."""
        return self._entry_id

    @property
    def configured_sources(self) -> frozenset[Metric]:
        """Return the source metrics that have a configured entity."""
        return frozenset(self._entity_to_metric.values())

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def _setup_listeners(self) -> None:
        entity_ids = list(self._entity_to_metric)
        if entity_ids:
            self._remove_listener = async_track_state_change_event(
                self._hass, entity_ids, self._on_state_change
            )
        # Prime from whatever the source entities already hold (e.g. restart).
        for entity_id in entity_ids:
            state = self._hass.states.get(entity_id)
            if state is not None:
                self._ingest(entity_id, state.state)
        self._recalculate()

    @callback
    def unload(self) -> None:
        """Remove listeners and drop subscribers."""
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None
        self._subscribers.clear()

    # ── Subscriptions ──────────────────────────────────────────────────────

    def subscribe(
        self, metric: Metric, callback_func: Callable[[float], None]
    ) -> CALLBACK_TYPE:
        """Subscribe to updates of a single metric; replays the current value."""
        self._subscribers.setdefault(metric, []).append(callback_func)

        current = self._derived.get(metric, self._sources.get(metric))
        if current is not None:
            callback_func(current)

        @callback
        def _remove() -> None:
            subs = self._subscribers.get(metric)
            if subs and callback_func in subs:
                subs.remove(callback_func)

        return _remove

    # ── State handling ─────────────────────────────────────────────────────

    @callback
    def _on_state_change(self, event: Event[EventStateChangedData]) -> None:
        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")
        if entity_id is None or new_state is None:
            return
        if self._ingest(entity_id, new_state.state):
            self._recalculate()

    def _ingest(self, entity_id: str, raw: Any) -> bool:
        """Store a raw source value; return True if it changed."""
        metric = self._entity_to_metric.get(entity_id)
        if metric is None:
            return False
        if raw in (STATE_UNAVAILABLE, STATE_UNKNOWN, None):
            return self._sources.pop(metric, None) is not None
        value = to_float(raw)
        if value is None or value <= 0:
            _LOGGER.debug("[%s] ignoring %s value %r", self._name, metric, raw)
            return False
        if self._sources.get(metric) == value:
            return False
        self._sources[metric] = value
        return True

    def _build_inputs(self) -> Inputs:
        return Inputs(
            height=self._height,
            age=self._age,
            gender=self._gender,
            weight=self._sources.get(Metric.WEIGHT),
            waist=self._sources.get(Metric.WAIST),
            hip=self._sources.get(Metric.HIP),
            neck=self._sources.get(Metric.NECK),
            calf=self._sources.get(Metric.CALF),
            wrist=self._sources.get(Metric.WRIST),
            thigh=self._sources.get(Metric.THIGH),
            chest=self._sources.get(Metric.CHEST),
            biceps=self._sources.get(Metric.BICEPS),
            ankle=self._sources.get(Metric.ANKLE),
        )

    def _recalculate(self) -> None:
        """Recompute all derived metrics and notify subscribers of changes."""
        new_derived = compute_all(self._build_inputs())

        # Publish raw sources too (so a source sensor can mirror the value).
        for metric, value in self._sources.items():
            self._notify(metric, value)

        # Drop derived metrics that can no longer be computed.
        for metric in list(self._derived):
            if metric not in new_derived:
                del self._derived[metric]

        for metric, value in new_derived.items():
            if self._derived.get(metric) != value:
                self._derived[metric] = value
                self._notify(metric, value)

    def _notify(self, metric: Metric, value: float) -> None:
        for sub in self._subscribers.get(metric, []):
            sub(value)
