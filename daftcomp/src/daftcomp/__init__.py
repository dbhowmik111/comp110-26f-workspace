"""Compose with ordinary lists, then launch a local, offline browser player."""

from ._core import HAT as HAT
from ._core import HOLD as HOLD
from ._core import KICK as KICK
from ._core import REST as REST
from ._core import SNARE as SNARE
from ._core import Registry, validate_launch
from ._notes import (
    A3,
    A4,
    A5,
    A6,
    B3,
    B4,
    B5,
    B6,
    C3,
    C4,
    C5,
    C6,
    D3,
    D4,
    D5,
    D6,
    E3,
    E4,
    E5,
    E6,
    F3,
    F4,
    F5,
    F6,
    G3,
    G4,
    G5,
    G6,
)
from ._server import launch, launch_studio

__all__ = [
    "HOLD",
    "REST",
    "KICK",
    "SNARE",
    "HAT",
    "add_track",
    "clear",
    "run",
    "studio",
    "A3",
    "A4",
    "A5",
    "A6",
    "B3",
    "B4",
    "B5",
    "B6",
    "C3",
    "C4",
    "C5",
    "C6",
    "D3",
    "D4",
    "D5",
    "D6",
    "E3",
    "E4",
    "E5",
    "E6",
    "F3",
    "F4",
    "F5",
    "F6",
    "G3",
    "G4",
    "G5",
    "G6",
]

_registry = Registry()


def add_track(*, name: str, notes: list[int], voice: str = "pulse") -> None:
    """Retain this list by identity; edits before run() are heard at playback."""
    _registry.add_track(name=name, notes=notes, voice=voice)


def clear() -> None:
    """Remove registrations without modifying any student list."""
    _registry.clear()


def run(
    *,
    title: str = "My Band",
    bpm: int = 120,
    steps_per_beat: int = 2,
    open_browser: bool = True,
    port: int = 0,
) -> None:
    """Validate and snapshot, then block until Ctrl+C stops the local server."""
    _registry.begin_run()
    try:
        validate_launch(port, open_browser)
        song = _registry.snapshot(title=title, bpm=bpm, steps_per_beat=steps_per_beat)
        launch(song, port=port, open_browser=open_browser)
    finally:
        _registry.end_run()


def studio(*, open_browser: bool = True, port: int = 0) -> None:
    """Open the keyboard studio, which turns what you play into lists to paste."""
    validate_launch(port, open_browser)
    launch_studio(port=port, open_browser=open_browser)
