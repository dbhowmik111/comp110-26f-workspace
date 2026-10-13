"""Check the installed packages without calling unfinished student code.

The workspace sync task runs this file. Your assignment checks are in
checks/; run them with:  uv run python -m pytest checks
"""

import importlib.util

import comp110_gui

from goodfire import science
from goodfire import terrain


def test_packages_installed() -> None:
    """The GUI library and the 3D packages are installed."""
    assert hasattr(comp110_gui, "Canvas")
    for name in ("PySide6", "ursina", "panda3d", "numpy"):
        assert importlib.util.find_spec(name) is not None, f"missing {name}"


def test_provided_modules_import() -> None:
    """The provided science and terrain modules load."""
    assert science.CELL_METERS == 30.0
    assert terrain.GRID_SIZE == 30
