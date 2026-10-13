"""Image resampling choices and their validation."""

from __future__ import annotations

from typing import Literal

from comp110_gui import validation

type Sampling = Literal["smooth", "nearest"]


def validate(value: Sampling) -> Sampling:
    """Validate the two supported image resampling choices."""
    validation.string(value, "sampling")
    if value not in ("smooth", "nearest"):
        raise ValueError("sampling must be 'smooth' or 'nearest'.")
    return value
