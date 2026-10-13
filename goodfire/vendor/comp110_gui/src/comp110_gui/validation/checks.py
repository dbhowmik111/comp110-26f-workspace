"""Small shared checks with student-facing error messages."""

import math
import threading


def string(value: object, name: str, *, nonblank: bool = False) -> str:
    """Validate text without silently converting another type."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string.")
    if nonblank and not value.strip():
        raise ValueError(f"{name} must contain a non-whitespace character.")
    return value


def boolean(value: object, name: str) -> bool:
    """Validate an explicit boolean value."""
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be True or False.")
    return value


def integer(value: object, name: str, *, minimum: int = 1) -> int:
    """Validate an integer, excluding booleans, with a lower bound."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, not a boolean.")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}.")
    return value


def number(value: object, name: str, *, positive: bool = False) -> float:
    """Validate a finite drawing coordinate or positive length."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be a number, not a boolean.")
    error: OverflowError
    try:
        result: float = float(value)
    except OverflowError as error:
        raise ValueError(f"{name} must be finite.") from error
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    if positive and result <= 0:
        raise ValueError(f"{name} must be positive.")
    return result


def callback(value: object, name: str) -> None:
    """Validate callability without rejecting opaque callable signatures."""
    if value is not None and not callable(value):
        raise TypeError(
            f"{name} expects a function or method, such as self.greet, or None."
        )


def main_thread() -> None:
    """Require Qt operations to stay on Python's main thread."""
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("GUI operations must run on the main thread.")
