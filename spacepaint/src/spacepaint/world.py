"""Pure, immutable Spacepaint commands and playback state."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from math import acos, cos, floor, isclose, isfinite, radians, sin, sqrt
from typing import TypeAlias

ColorRGB: TypeAlias = tuple[float, float, float]

BASE_LINEAR_SPEED = 3.5
BASE_ANGULAR_SPEED = 120.0
FADE_TRANSITION_SECONDS = 0.55
EPSILON = 1e-9
ARC_SAMPLE_DEGREES = 4.0
FILL_PLANE_TOLERANCE = 1e-6
DEFAULT_FILL_OPACITY = 72 / 255


@dataclass(frozen=True, slots=True)
class Vec3:
    x: float
    y: float
    z: float

    def __add__(self, other: Vec3) -> Vec3:
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vec3) -> Vec3:
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> Vec3:
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __neg__(self) -> Vec3:
        return Vec3(-self.x, -self.y, -self.z)

    def dot(self, other: Vec3) -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: Vec3) -> Vec3:
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    @property
    def length(self) -> float:
        return sqrt(self.dot(self))

    def normalized(self) -> Vec3:
        magnitude = self.length
        if magnitude <= EPSILON:
            return Vec3(0.0, 0.0, 0.0)
        return self * (1.0 / magnitude)

    def lerp(self, other: Vec3, amount: float) -> Vec3:
        return self + (other - self) * amount


@dataclass(frozen=True, slots=True)
class Quaternion:
    w: float
    x: float
    y: float
    z: float

    @staticmethod
    def identity() -> Quaternion:
        return Quaternion(1.0, 0.0, 0.0, 0.0)

    @staticmethod
    def axis_angle(axis: Vec3, degrees: float) -> Quaternion:
        unit = axis.normalized()
        half_angle = radians(degrees) / 2
        scale = sin(half_angle)
        return Quaternion(
            cos(half_angle), unit.x * scale, unit.y * scale, unit.z * scale
        ).normalized()

    def __mul__(self, other: Quaternion) -> Quaternion:
        return Quaternion(
            self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z,
            self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y,
            self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x,
            self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w,
        )

    def normalized(self) -> Quaternion:
        magnitude = sqrt(
            self.w * self.w + self.x * self.x + self.y * self.y + self.z * self.z
        )
        if magnitude <= EPSILON:
            return Quaternion.identity()
        return Quaternion(
            self.w / magnitude,
            self.x / magnitude,
            self.y / magnitude,
            self.z / magnitude,
        )

    def conjugate(self) -> Quaternion:
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def rotate(self, vector: Vec3) -> Vec3:
        rotated = (
            self * Quaternion(0.0, vector.x, vector.y, vector.z) * self.conjugate()
        )
        return Vec3(rotated.x, rotated.y, rotated.z)

    def slerp(self, other: Quaternion, amount: float) -> Quaternion:
        target = other
        dot = (
            self.w * target.w
            + self.x * target.x
            + self.y * target.y
            + self.z * target.z
        )
        if dot < 0:
            target = Quaternion(-target.w, -target.x, -target.y, -target.z)
            dot = -dot
        dot = min(1.0, max(-1.0, dot))
        if dot > 0.9995:
            return Quaternion(
                self.w + amount * (target.w - self.w),
                self.x + amount * (target.x - self.x),
                self.y + amount * (target.y - self.y),
                self.z + amount * (target.z - self.z),
            ).normalized()
        angle = acos(dot)
        denominator = sin(angle)
        left = sin((1 - amount) * angle) / denominator
        right = sin(amount * angle) / denominator
        return Quaternion(
            self.w * left + target.w * right,
            self.x * left + target.x * right,
            self.y * left + target.y * right,
            self.z * left + target.z * right,
        ).normalized()


class RotationKind(Enum):
    YAW = "yaw"
    PITCH = "pitch"
    ROLL = "roll"


@dataclass(frozen=True, slots=True)
class MoveForwardCommand:
    distance: float


@dataclass(frozen=True, slots=True)
class ArcCommand:
    radius: float
    degrees: float


@dataclass(frozen=True, slots=True)
class RotateCommand:
    kind: RotationKind
    degrees: float


@dataclass(frozen=True, slots=True)
class BeamOnCommand:
    enabled: bool
    fade_after: float | None = None


@dataclass(frozen=True, slots=True)
class BeamColorCommand:
    name: str
    rgb: ColorRGB


@dataclass(frozen=True, slots=True)
class BeamWidthCommand:
    width: float


@dataclass(frozen=True, slots=True)
class ClearBeamsCommand:
    pass


@dataclass(frozen=True, slots=True)
class FillOnCommand:
    enabled: bool
    opacity: float = DEFAULT_FILL_OPACITY


@dataclass(frozen=True, slots=True)
class SetSpeedCommand:
    multiplier: float


Command: TypeAlias = (
    MoveForwardCommand
    | ArcCommand
    | RotateCommand
    | BeamOnCommand
    | BeamColorCommand
    | BeamWidthCommand
    | ClearBeamsCommand
    | FillOnCommand
    | SetSpeedCommand
)


@dataclass(frozen=True, slots=True)
class ShipState:
    """Predicted ship state after the commands queued so far."""

    position: Vec3
    orientation: Quaternion
    beam_on: bool = False

    @property
    def forward(self) -> Vec3:
        return self.orientation.rotate(Vec3(1.0, 0.0, 0.0)).normalized()

    @property
    def left(self) -> Vec3:
        return self.orientation.rotate(Vec3(0.0, 1.0, 0.0)).normalized()

    @property
    def up(self) -> Vec3:
        return self.orientation.rotate(Vec3(0.0, 0.0, 1.0)).normalized()


def initial_ship_state() -> ShipState:
    """Return the state of a ship before any commands have been queued."""
    return ShipState(Vec3(0.0, 0.0, 0.0), Quaternion.identity())


@dataclass(frozen=True, slots=True)
class BeamStyle:
    color_name: str
    color: ColorRGB
    width: float
    fade_after: float | None


@dataclass(frozen=True, slots=True)
class BeamSample:
    position: Vec3
    emitted_at: float


@dataclass(frozen=True, slots=True)
class BeamStroke:
    samples: tuple[BeamSample, ...]
    style: BeamStyle


@dataclass(frozen=True, slots=True)
class FillRegion:
    vertices: tuple[Vec3, ...]
    color: ColorRGB
    plane_normal: Vec3 | None = None
    opacity: float = DEFAULT_FILL_OPACITY


@dataclass(frozen=True, slots=True)
class ActiveMove:
    start: Vec3
    end: Vec3
    duration: float
    elapsed: float = 0.0


@dataclass(frozen=True, slots=True)
class ActiveRotation:
    start: Quaternion
    end: Quaternion
    kind: RotationKind
    degrees: float
    duration: float
    elapsed: float = 0.0


@dataclass(frozen=True, slots=True)
class ActiveArc:
    start: ShipState
    center: Vec3
    axis: Vec3
    degrees: float
    duration: float
    elapsed: float = 0.0


ActiveMotion: TypeAlias = ActiveMove | ActiveRotation | ActiveArc


@dataclass(frozen=True, slots=True)
class WorldState:
    pose: ShipState
    beam_enabled: bool
    beam_style: BeamStyle
    strokes: tuple[BeamStroke, ...]
    stroke_open: bool
    fill_enabled: bool
    fill_opacity: float
    fills: tuple[FillRegion, ...]
    fill_open: bool
    speed_multiplier: float
    command_index: int
    active_motion: ActiveMotion | None
    elapsed_time: float
    paused: bool
    completed: bool


def initial_world_state() -> WorldState:
    return WorldState(
        pose=initial_ship_state(),
        beam_enabled=False,
        beam_style=BeamStyle("cyan", (0.12, 0.95, 1.0), 0.12, None),
        strokes=(),
        stroke_open=False,
        fill_enabled=False,
        fill_opacity=DEFAULT_FILL_OPACITY,
        fills=(),
        fill_open=False,
        speed_multiplier=1.0,
        command_index=0,
        active_motion=None,
        elapsed_time=0.0,
        paused=False,
        completed=False,
    )


def set_paused(state: WorldState, paused: bool) -> WorldState:
    return replace(state, paused=paused)


def beam_sample_alpha(sample: BeamSample, style: BeamStyle, now: float) -> float:
    if style.fade_after is None:
        return 1.0
    age = max(0.0, now - sample.emitted_at)
    if age <= style.fade_after:
        return 1.0
    return max(0.0, 1.0 - (age - style.fade_after) / FADE_TRANSITION_SECONDS)


def _prune_faded(state: WorldState) -> WorldState:
    retained: list[BeamStroke] = []
    for stroke in state.strokes:
        samples = tuple(
            sample
            for sample in stroke.samples
            if beam_sample_alpha(sample, stroke.style, state.elapsed_time) > 0
        )
        if samples:
            retained.append(BeamStroke(samples, stroke.style))
    return replace(state, strokes=tuple(retained))


def _plane_normal(vertices: tuple[Vec3, ...]) -> Vec3 | None:
    if len(vertices) < 3:
        return None
    base = vertices[0]
    for first_index in range(1, len(vertices) - 1):
        first = vertices[first_index] - base
        for second_index in range(first_index + 1, len(vertices)):
            normal = first.cross(vertices[second_index] - base)
            if normal.length > EPSILON:
                return normal.normalized()
    return None


def _append_fill_vertex(state: WorldState, position: Vec3) -> WorldState:
    if not state.fill_enabled:
        return replace(state, fill_open=False)
    if not state.fill_open or not state.fills:
        region = FillRegion(
            (position,),
            state.beam_style.color,
            opacity=state.fill_opacity,
        )
        return replace(state, fills=state.fills + (region,), fill_open=True)

    region = state.fills[-1]
    if not region.vertices:
        updated = replace(
            region,
            vertices=(position,),
            color=state.beam_style.color,
            opacity=state.fill_opacity,
        )
        return replace(state, fills=state.fills[:-1] + (updated,))
    origin = region.vertices[0]
    last = region.vertices[-1]
    if (last - position).length <= EPSILON:
        return state
    extent = max(
        1.0,
        max((vertex - origin).length for vertex in region.vertices),
        (position - origin).length,
    )
    if (
        len(region.vertices) >= 3
        and (origin - position).length <= FILL_PLANE_TOLERANCE * extent
    ):
        return replace(state, fill_open=False)

    normal = region.plane_normal
    if normal is not None:
        plane_distance = abs((position - origin).dot(normal))
        if plane_distance > FILL_PLANE_TOLERANCE * extent:
            new_region = FillRegion(
                (last, position),
                state.beam_style.color,
                opacity=state.fill_opacity,
            )
            return replace(state, fills=state.fills + (new_region,), fill_open=True)

    vertices = region.vertices + (position,)
    updated = replace(
        region, vertices=vertices, plane_normal=normal or _plane_normal(vertices)
    )
    return replace(state, fills=state.fills[:-1] + (updated,))


def _append_sample(
    state: WorldState, position: Vec3, emitted_at: float | None = None
) -> WorldState:
    painted = state
    if state.beam_enabled:
        sample = BeamSample(
            position, state.elapsed_time if emitted_at is None else emitted_at
        )
        if state.stroke_open and state.strokes:
            last = state.strokes[-1]
            if (
                not last.samples
                or (last.samples[-1].position - position).length > EPSILON
            ):
                updated = BeamStroke(last.samples + (sample,), last.style)
                painted = replace(state, strokes=state.strokes[:-1] + (updated,))
        else:
            painted = replace(
                state,
                strokes=state.strokes + (BeamStroke((sample,), state.beam_style),),
                stroke_open=True,
            )
    else:
        painted = replace(state, stroke_open=False)
    return _append_fill_vertex(painted, position)


def _target_orientation(orientation: Quaternion, command: RotateCommand) -> Quaternion:
    # Body-space axes: +X forward, +Y left, and +Z up. Positive command
    # degrees mean yaw left, pitch up, or roll left, respectively.
    if command.kind is RotationKind.YAW:
        axis = Vec3(0.0, 0.0, 1.0)
    elif command.kind is RotationKind.PITCH:
        axis = Vec3(0.0, -1.0, 0.0)
    else:
        axis = Vec3(-1.0, 0.0, 0.0)
    rotation = Quaternion.axis_angle(axis, command.degrees)
    return (orientation * rotation).normalized()


def _arc_pose(active: ActiveArc, amount: float) -> ShipState:
    rotation = Quaternion.axis_angle(active.axis, active.degrees * amount)
    position = active.center + rotation.rotate(active.start.position - active.center)
    orientation = (rotation * active.start.orientation).normalized()
    return replace(active.start, position=position, orientation=orientation)


def _arc_parameters(state: ShipState, command: ArcCommand) -> tuple[Vec3, Vec3, float]:
    center = state.position + state.left * command.radius
    signed_degrees = command.degrees if command.radius > 0 else -command.degrees
    return center, state.up, signed_degrees


def apply_command_to_ship_state(state: ShipState, command: Command) -> ShipState:
    """Return the pose after ``command`` completes, without animating it."""
    if isinstance(command, MoveForwardCommand):
        return replace(
            state, position=state.position + state.forward * command.distance
        )
    if isinstance(command, RotateCommand):
        return replace(
            state, orientation=_target_orientation(state.orientation, command)
        )
    if isinstance(command, ArcCommand):
        center, axis, signed_degrees = _arc_parameters(state, command)
        active = ActiveArc(state, center, axis, signed_degrees, 0.0)
        return _arc_pose(active, 1.0)
    if isinstance(command, BeamOnCommand):
        return replace(state, beam_on=command.enabled)
    return state


def _begin_motion(state: WorldState, command: Command) -> WorldState:
    position = state.pose.position
    end: Vec3 | None = None
    if isinstance(command, MoveForwardCommand):
        end = apply_command_to_ship_state(state.pose, command).position
    if end is not None:
        distance = (end - position).length
        duration = (
            distance / (BASE_LINEAR_SPEED * state.speed_multiplier)
            if distance > EPSILON
            else 0.0
        )
        active = ActiveMove(position, end, duration)
        started = replace(state, active_motion=active)
        should_record = (
            state.beam_enabled or state.fill_enabled
        ) and distance > EPSILON
        return _append_sample(started, position) if should_record else started
    if isinstance(command, ArcCommand):
        center, axis, signed_degrees = _arc_parameters(state.pose, command)
        distance = abs(radians(command.degrees) * command.radius)
        duration = (
            distance / (BASE_LINEAR_SPEED * state.speed_multiplier)
            if distance > EPSILON
            else 0.0
        )
        active = ActiveArc(state.pose, center, axis, signed_degrees, duration)
        started = replace(state, active_motion=active)
        should_record = (
            state.beam_enabled or state.fill_enabled
        ) and distance > EPSILON
        return _append_sample(started, position) if should_record else started
    if isinstance(command, RotateCommand):
        target = apply_command_to_ship_state(state.pose, command).orientation
        duration = abs(command.degrees) / (BASE_ANGULAR_SPEED * state.speed_multiplier)
        return replace(
            state,
            active_motion=ActiveRotation(
                state.pose.orientation,
                target,
                command.kind,
                command.degrees,
                duration,
            ),
        )
    return state


def _apply_instant(state: WorldState, command: Command) -> WorldState:
    next_index = state.command_index + 1
    if isinstance(command, BeamOnCommand):
        style = (
            replace(state.beam_style, fade_after=command.fade_after)
            if command.enabled
            else state.beam_style
        )
        return replace(
            state,
            pose=apply_command_to_ship_state(state.pose, command),
            beam_enabled=command.enabled,
            beam_style=style,
            stroke_open=False,
            command_index=next_index,
        )
    if isinstance(command, BeamColorCommand):
        style = replace(state.beam_style, color_name=command.name, color=command.rgb)
        return replace(
            state, beam_style=style, stroke_open=False, command_index=next_index
        )
    if isinstance(command, BeamWidthCommand):
        return replace(
            state,
            beam_style=replace(state.beam_style, width=command.width),
            stroke_open=False,
            command_index=next_index,
        )
    if isinstance(command, ClearBeamsCommand):
        return replace(
            state,
            strokes=(),
            stroke_open=False,
            fills=(),
            fill_open=False,
            command_index=next_index,
        )
    if isinstance(command, FillOnCommand):
        return replace(
            state,
            fill_enabled=command.enabled and command.opacity > 0,
            fill_opacity=command.opacity if command.enabled else 0.0,
            fill_open=False,
            command_index=next_index,
        )
    if isinstance(command, SetSpeedCommand):
        if command.multiplier == 0:
            return replace(state, paused=True, command_index=next_index)
        return replace(
            state, speed_multiplier=command.multiplier, command_index=next_index
        )
    return state


def _finish_active(state: WorldState) -> WorldState:
    active = state.active_motion
    if isinstance(active, ActiveMove):
        return replace(
            state,
            pose=replace(state.pose, position=active.end),
            active_motion=None,
            command_index=state.command_index + 1,
        )
    if isinstance(active, ActiveRotation):
        return replace(
            state,
            pose=replace(state.pose, orientation=active.end),
            active_motion=None,
            command_index=state.command_index + 1,
        )
    if isinstance(active, ActiveArc):
        pose = _arc_pose(active, 1.0)
        moved = replace(state, pose=pose)
        sweep = abs(active.degrees)
        sampled_final = sweep > EPSILON and isclose(
            sweep / ARC_SAMPLE_DEGREES,
            round(sweep / ARC_SAMPLE_DEGREES),
        )
        if sweep > EPSILON and not sampled_final:
            moved = _append_sample(moved, pose.position)
        return replace(moved, active_motion=None, command_index=state.command_index + 1)
    return state


def _advance_active(state: WorldState, available: float) -> tuple[WorldState, float]:
    active = state.active_motion
    if active is None:
        return state, available
    remaining_duration = max(0.0, active.duration - active.elapsed)
    consumed = min(available, remaining_duration)
    new_elapsed = active.elapsed + consumed
    amount = (
        1.0 if active.duration <= EPSILON else min(1.0, new_elapsed / active.duration)
    )
    timed = replace(state, elapsed_time=state.elapsed_time + consumed)
    old_amount = (
        1.0
        if active.duration <= EPSILON
        else min(1.0, active.elapsed / active.duration)
    )
    if isinstance(active, ActiveMove):
        position = active.start.lerp(active.end, amount)
        timed = replace(
            timed,
            pose=replace(timed.pose, position=position),
            active_motion=replace(active, elapsed=new_elapsed),
        )
        timed = _append_sample(timed, position)
    elif isinstance(active, ActiveRotation):
        orientation = _target_orientation(
            active.start,
            RotateCommand(active.kind, active.degrees * amount),
        )
        timed = replace(
            timed,
            pose=replace(timed.pose, orientation=orientation),
            active_motion=replace(active, elapsed=new_elapsed),
        )
    else:
        pose = _arc_pose(active, amount)
        timed = replace(
            timed,
            pose=pose,
            active_motion=replace(active, elapsed=new_elapsed),
        )
        sweep = abs(active.degrees)
        if sweep > EPSILON and amount > old_amount:
            first_step = floor(old_amount * sweep / ARC_SAMPLE_DEGREES) + 1
            final_step = floor(amount * sweep / ARC_SAMPLE_DEGREES)
            for step in range(first_step, final_step + 1):
                sample_amount = min(1.0, step * ARC_SAMPLE_DEGREES / sweep)
                sample_pose = _arc_pose(active, sample_amount)
                sample_time = (
                    state.elapsed_time
                    - active.elapsed
                    + sample_amount * active.duration
                )
                timed = _append_sample(timed, sample_pose.position, sample_time)
    if amount >= 1.0 or isclose(amount, 1.0):
        timed = _finish_active(timed)
    return timed, available - consumed


def advance(
    state: WorldState,
    commands: tuple[Command, ...],
    delta_seconds: float,
    *,
    stop_before_command_index: int | None = None,
) -> WorldState:
    """Advance playback, optionally stopping exactly at a command boundary."""
    if not isfinite(delta_seconds) or delta_seconds < 0:
        raise ValueError("delta_seconds must be finite and non-negative")
    if stop_before_command_index is not None and stop_before_command_index < 0:
        raise ValueError("stop_before_command_index must be non-negative")
    if state.paused:
        return state

    current = state
    remaining = delta_seconds
    safety = 0
    while safety < len(commands) * 2 + 16:
        safety += 1
        if (
            stop_before_command_index is not None
            and current.active_motion is None
            and current.command_index >= stop_before_command_index
        ):
            break
        if current.active_motion is not None:
            current, remaining = _advance_active(current, remaining)
            if current.active_motion is not None or remaining <= EPSILON:
                break
            continue
        if current.command_index >= len(commands):
            current = replace(
                current,
                elapsed_time=current.elapsed_time + remaining,
                completed=True,
            )
            remaining = 0.0
            break
        command = commands[current.command_index]
        begun = _begin_motion(current, command)
        if begun.active_motion is not None:
            current = begun
            if begun.active_motion.duration <= EPSILON:
                current = _finish_active(current)
                continue
            if remaining <= EPSILON:
                break
            continue
        current = _apply_instant(current, command)
        if current.paused:
            break
    return _prune_faded(current)


def replay_to_command(commands: tuple[Command, ...], command_index: int) -> WorldState:
    """Rebuild the exact state immediately before ``command_index``."""
    target = min(max(0, command_index), len(commands))
    current = initial_world_state()
    while current.command_index < target:
        before = current
        current = advance(
            replace(current, paused=False),
            commands,
            1_000_000.0,
            stop_before_command_index=target,
        )
        if (
            current.command_index == before.command_index
            and current.active_motion == before.active_motion
        ):
            raise RuntimeError("could not replay to command boundary")
    return replace(current, paused=False, completed=False)


def replay_to_completion(commands: tuple[Command, ...]) -> WorldState:
    """Rebuild the state after every command, continuing through breakpoints."""
    final_boundary = replay_to_command(commands, len(commands))
    return advance(final_boundary, commands, 0.0)


def command_name(state: WorldState, commands: tuple[Command, ...]) -> str:
    if state.completed or state.command_index >= len(commands):
        return "complete"
    command = commands[state.command_index]
    if isinstance(command, MoveForwardCommand):
        return "forward" if command.distance >= 0 else "backward"
    if isinstance(command, ArcCommand):
        return "arc"
    if isinstance(command, RotateCommand):
        return command.kind.value
    if isinstance(command, BeamOnCommand):
        return "beam"
    if isinstance(command, BeamColorCommand):
        return "beam_color"
    if isinstance(command, BeamWidthCommand):
        return "beam_width"
    if isinstance(command, ClearBeamsCommand):
        return "clear_beams"
    if isinstance(command, FillOnCommand):
        return "fill"
    return "speed"
