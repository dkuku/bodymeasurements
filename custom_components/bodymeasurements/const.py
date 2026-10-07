"""Constants for the Body Measurements integration."""

from homeassistant.const import Platform

MIN_REQUIRED_HA_VERSION = "2026.3.0"
NAME = "Body Measurements"
DOMAIN = "bodymeasurements"
VERSION = "0.4.0"
ISSUE_URL = "https://github.com/dkuku/bodymeasurements/issues"

# System keys for hass.data[DOMAIN]
HANDLERS = "handlers"

# ---------------------------------------------------------------------------
# User configuration
# ---------------------------------------------------------------------------
# Static profile data (set once, editable via the options flow).
CONF_BIRTHDAY = "birthday"
CONF_GENDER = "gender"
CONF_HEIGHT = "height"
CONF_BODY_FAT_METHOD = "body_fat_method"
DEFAULT_BODY_FAT_METHOD = "calibrated"

# Source measurement entities (input_number / number / sensor).
# The Metric enum reuses these string keys for the raw source metrics.
CONF_SENSOR_WEIGHT = "weight"
CONF_SENSOR_WAIST = "waist"
CONF_SENSOR_HIP = "hip"
CONF_SENSOR_NECK = "neck"
CONF_SENSOR_CALF = "calf"
CONF_SENSOR_WRIST = "wrist"
CONF_SENSOR_THIGH = "thigh"
CONF_SENSOR_CHEST = "chest"
CONF_SENSOR_BICEPS = "biceps"
CONF_SENSOR_ANKLE = "ankle"

# Every optional source, in display order.
CONF_MEASUREMENT_SOURCES = (
    CONF_SENSOR_WAIST,
    CONF_SENSOR_HIP,
    CONF_SENSOR_NECK,
    CONF_SENSOR_CALF,
    CONF_SENSOR_WRIST,
    CONF_SENSOR_THIGH,
    CONF_SENSOR_CHEST,
    CONF_SENSOR_BICEPS,
    CONF_SENSOR_ANKLE,
)

# ---------------------------------------------------------------------------
# Validation constraints
# ---------------------------------------------------------------------------
CONSTRAINT_HEIGHT_MIN = 50
CONSTRAINT_HEIGHT_MAX = 250
CONSTRAINT_WEIGHT_MIN = 10
CONSTRAINT_WEIGHT_MAX = 300
# Plausible human circumference range (cm) — guards against unit mistakes.
CONSTRAINT_CIRCUMFERENCE_MIN = 10
CONSTRAINT_CIRCUMFERENCE_MAX = 250

# ---------------------------------------------------------------------------
# Home Assistant
# ---------------------------------------------------------------------------
PLATFORMS: list[Platform] = [Platform.SENSOR]

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
