"""Utility helpers for the Body Measurements integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def to_float(val: Any, default: float | None = None) -> float | None:
    """Convert a value to float if possible, else return ``default``."""
    if isinstance(val, bool):
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except (ValueError, TypeError):
            return default
    return default


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp ``value`` into the inclusive ``[minimum, maximum]`` range."""
    return max(minimum, min(maximum, value))


def get_age(date_str: str) -> int:
    """Return the current age in whole years from a ``YYYY-MM-DD`` birthday."""
    try:
        born = datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return 0
    today = datetime.today()
    age = today.year - born.year
    if (today.month, today.day) < (born.month, born.day):
        age -= 1
    return max(age, 0)
