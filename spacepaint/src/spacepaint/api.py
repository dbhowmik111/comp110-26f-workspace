"""Student-facing command recorder with no rendering dependencies."""

from __future__ import annotations

from math import atan2, degrees, isfinite
from typing import Protocol, Self

from spacepaint.world import (
    DEFAULT_FILL_OPACITY,
    ArcCommand,
    BeamColorCommand,
    BeamOnCommand,
    BeamWidthCommand,
    ClearBeamsCommand,
    Command,
    FillOnCommand,
    MoveForwardCommand,
    Quaternion,
    RotateCommand,
    RotationKind,
    SetSpeedCommand,
    ShipState,
    Vec3,
    apply_command_to_ship_state,
    initial_ship_state,
)

ColorRGB = tuple[float, float, float]

NAMED_COLORS: dict[str, ColorRGB] = {
    "white": (1.0, 1.0, 1.0),
    "red": (1.0, 0.18, 0.16),
    "orange": (1.0, 0.48, 0.12),
    "yellow": (1.0, 0.88, 0.18),
    "green": (0.20, 1.0, 0.48),
    "cyan": (0.12, 0.95, 1.0),
    "blue": (0.20, 0.48, 1.0),
    "purple": (0.58, 0.28, 1.0),
    "magenta": (1.0, 0.20, 0.82),
    "pink": (1.0, 0.38, 0.66),
}


class Ship(Protocol):
    """The small, explicit interface given to a student program."""

    @property
    def state(self) -> ShipState: ...

    @property
    def position(self) -> Vec3: ...

    @property
    def orientation(self) -> Quaternion: ...

    @property
    def x(self) -> float: ...

    @property
    def y(self) -> float: ...

    @property
    def z(self) -> float: ...

    @property
    def forward_vector(self) -> Vec3: ...

    @property
    def left_vector(self) -> Vec3: ...

    @property
    def up_vector(self) -> Vec3: ...

    @property
    def heading_x_y(self) -> float: ...

    def forward(self, units: float) -> None: ...
    def backward(self, distance: float) -> None: ...
    def arc(self, radius: float, degrees: float) -> None: ...
    def turn(self, degrees: float) -> None: ...
    def yaw_left(self, degrees: float) -> None: ...
    def yaw_right(self, degrees: float) -> None: ...
    def pitch_up(self, degrees: float) -> None: ...
    def pitch_down(self, degrees: float) -> None: ...
    def roll_left(self, degrees: float) -> None: ...
    def roll_right(self, degrees: float) -> None: ...
    def beam(self, on: bool, *, fade_after: float | None = None) -> None: ...
    def beam_color(self, value: str) -> None: ...
    def beam_width(self, width: float) -> None: ...
    def clear_beams(self) -> None: ...
    def fill(self, on: bool, opacity: float = DEFAULT_FILL_OPACITY) -> None: ...
    def speed(self, multiplier: float) -> None: ...


def _finite(value: float, name: str) -> float:
    resolved = float(value)
    if not isfinite(resolved):
        raise ValueError(f"{name} must be a finite number")
    return resolved


def _positive(value: float, name: str) -> float:
    resolved = _finite(value, name)
    if resolved <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return resolved


def _nonnegative(value: float, name: str) -> float:
    resolved = _finite(value, name)
    if resolved < 0:
        raise ValueError(f"{name} must be zero or greater")
    return resolved


def _nonzero(value: float, name: str) -> float:
    resolved = _finite(value, name)
    if resolved == 0:
        raise ValueError(f"{name} must not be zero")
    return resolved


def _unit_interval(value: float, name: str) -> float:
    resolved = _finite(value, name)
    if not 0 <= resolved <= 1:
        raise ValueError(f"{name} must be between 0 and 1")
    return resolved


def parse_color(value: str) -> tuple[str, ColorRGB]:
    """Normalize a named or hexadecimal student color."""
    normalized = value.strip().lower()
    if normalized in NAMED_COLORS:
        return normalized, NAMED_COLORS[normalized]
    if len(normalized) == 7 and normalized.startswith("#"):
        try:
            channels = tuple(
                int(normalized[index : index + 2], 16) / 255 for index in (1, 3, 5)
            )
        except ValueError as error:
            raise ValueError(
                f"invalid beam color {value!r}; use a named color or #RRGGBB"
            ) from error
        red, green, blue = channels
        return normalized, (red, green, blue)
    raise ValueError(f"invalid beam color {value!r}; use a named color or #RRGGBB")


class CommandRecorder:
    """Concrete Ship implementation that records commands and predicts state."""

    def __init__(self) -> None:
        self._commands: list[Command] = []
        self._state = initial_ship_state()

    @property
    def commands(self) -> tuple[Command, ...]:
        return tuple(self._commands)

    @property
    def state(self) -> ShipState:
        return self._state

    @property
    def position(self) -> Vec3:
        """Return the predicted position object from the ship state."""
        return self._state.position

    @property
    def orientation(self) -> Quaternion:
        """Return the predicted orientation object from the ship state."""
        return self._state.orientation

    @property
    def x(self) -> float:
        """Return the predicted x-coordinate after all queued commands."""
        return self.position.x

    @property
    def y(self) -> float:
        """Return the predicted y-coordinate after all queued commands."""
        return self.position.y

    @property
    def z(self) -> float:
        """Return the predicted z-coordinate after all queued commands."""
        return self.position.z

    @property
    def forward_vector(self) -> Vec3:
        """Return the predicted forward direction from the ship state."""
        return self._state.forward

    @property
    def left_vector(self) -> Vec3:
        """Return the predicted left direction from the ship state."""
        return self._state.left

    @property
    def up_vector(self) -> Vec3:
        """Return the predicted up direction from the ship state."""
        return self._state.up

    @property
    def heading_x_y(self) -> float:
        """Return the signed x/y heading in degrees from +X toward +Y."""
        forward = self.forward_vector
        return degrees(atan2(forward.y, forward.x))

    def _append(self, command: Command) -> Self:
        self._commands.append(command)
        self._state = apply_command_to_ship_state(self._state, command)
        return self

    def forward(self, units: float) -> None:
        self._append(MoveForwardCommand(_finite(units, "units")))

    def backward(self, distance: float) -> None:
        self._append(MoveForwardCommand(-_finite(distance, "distance")))

    def arc(self, radius: float, degrees: float) -> None:
        """Follow a turtle-style arc; a negative radius bends right."""
        self._append(
            ArcCommand(_nonzero(radius, "radius"), _finite(degrees, "degrees"))
        )

    def turn(self, degrees: float) -> None:
        """Turn by signed degrees; positive is counterclockwise."""
        self._append(RotateCommand(RotationKind.YAW, _finite(degrees, "degrees")))

    def yaw_left(self, degrees: float) -> None:
        self._append(RotateCommand(RotationKind.YAW, _finite(degrees, "degrees")))

    def yaw_right(self, degrees: float) -> None:
        self._append(RotateCommand(RotationKind.YAW, -_finite(degrees, "degrees")))

    def pitch_up(self, degrees: float) -> None:
        self._append(RotateCommand(RotationKind.PITCH, _finite(degrees, "degrees")))

    def pitch_down(self, degrees: float) -> None:
        self._append(RotateCommand(RotationKind.PITCH, -_finite(degrees, "degrees")))

    def roll_left(self, degrees: float) -> None:
        self._append(RotateCommand(RotationKind.ROLL, _finite(degrees, "degrees")))

    def roll_right(self, degrees: float) -> None:
        self._append(RotateCommand(RotationKind.ROLL, -_finite(degrees, "degrees")))

    def beam(self, on: bool, *, fade_after: float | None = None) -> None:
        resolved = None if fade_after is None else _positive(fade_after, "fade_after")
        self._append(BeamOnCommand(on, resolved))

    def beam_color(self, value: str) -> None:
        name, rgb = parse_color(value)
        self._append(BeamColorCommand(name, rgb))

    def beam_width(self, width: float) -> None:
        self._append(BeamWidthCommand(_positive(width, "width")))

    def clear_beams(self) -> None:
        self._append(ClearBeamsCommand())

    def fill(self, on: bool, opacity: float = DEFAULT_FILL_OPACITY) -> None:
        """Enable planar fill at ``opacity``, or disable it when false."""
        resolved = _unit_interval(opacity, "opacity")
        self._append(FillOnCommand(on, resolved))

    def speed(self, multiplier: float) -> None:
        self._append(SetSpeedCommand(_nonnegative(multiplier, "multiplier")))
