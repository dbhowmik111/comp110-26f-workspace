"""Public Spacepaint package API."""

import sys
from inspect import currentframe
from types import ModuleType

from spacepaint.api import CommandRecorder, Ship
from spacepaint.world import Quaternion, ShipState, Vec3

__all__ = [
    "CommandRecorder",
    "Quaternion",
    "Ship",
    "ShipState",
    "Vec3",
    "start_spacepaint",
]


def start_spacepaint() -> None:
    """Launch Spacepaint using ``main`` from the calling student module."""
    frame = currentframe()
    try:
        caller = None if frame is None else frame.f_back
        module_name = None if caller is None else caller.f_globals.get("__name__")
        student_module = (
            sys.modules.get(module_name) if isinstance(module_name, str) else None
        )
        if not isinstance(student_module, ModuleType):
            raise TypeError(
                "could not identify the module that called "
                "spacepaint.start_spacepaint()"
            )
    finally:
        del frame

    from spacepaint.main import start_spacepaint as run

    run(student_module=student_module)
