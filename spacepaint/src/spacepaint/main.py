"""Ursina application layer for Spacepaint.

This is intentionally the only Spacepaint module that talks to the graphics
stack, window, mouse, keyboard, or render entities.
"""

from __future__ import annotations

import sys
import traceback
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, replace
from enum import Enum
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from math import atan, exp, isfinite, radians, sin, sqrt, tan
from os import PathLike
from pathlib import Path
from random import Random
from types import ModuleType
from typing import Any, Protocol, TypeAlias, cast

from spacepaint.api import CommandRecorder, Ship
from spacepaint.bloom import (
    NativeBloomConfig,
    NativeBloomPipeline,
    prefers_native_bloom,
    validate_multisamples,
)
from spacepaint.geometry import (
    FillMeshData,
    TrailMeshData,
    build_fill_mesh,
    build_trail_mesh,
)
from spacepaint.world import (
    BeamStroke,
    Command,
    FillRegion,
    Quaternion,
    SetSpeedCommand,
    Vec3,
    WorldState,
    advance,
    beam_sample_alpha,
    command_name,
    initial_world_state,
    replay_to_command,
    replay_to_completion,
    set_paused,
)

_panda = cast(Any, import_module("panda3d.core"))
_panda.loadPrcFileData("", "notify-level-pnmimage error")

BACKGROUND_SPHERE_SCALE_MARGIN = 2.5
AXIS_MAJOR_TICK_INTERVAL = 5
AXIS_MINOR_TICK_INTERVAL = 1
AXIS_TICK_LABEL_SCALE = 40.0
AXIS_NAME_LABEL_SCALE = 54.0
AXIS_NAME_DISTANCE = 12.5
AXIS_LABEL_REFERENCE_DISTANCE = 75.0
ARTWORK_SHIP_BOUND_RADIUS = 1.25
ARTWORK_BEAM_AURA_HALF_WIDTH_SCALE = 1.9

Point3: TypeAlias = tuple[float, float, float]
Bounds3: TypeAlias = tuple[Point3, Point3]


class CameraView(Enum):
    SHIP = "SHIP"
    ART = "ART"


class AxesView(Enum):
    HIDDEN = "OFF"
    XY = "X/Y"
    XYZ = "X/Y/Z"


def fill_rgba32(region: FillRegion) -> tuple[int, int, int, int]:
    """Return the brightened fill color and its student-selected alpha."""
    red, green, blue = region.color
    return (
        round((red + (1 - red) * 0.08) * 255),
        round((green + (1 - green) * 0.08) * 255),
        round((blue + (1 - blue) * 0.08) * 255),
        round(region.opacity * 255),
    )


@dataclass(frozen=True, slots=True)
class GameConfig:
    title: str = "Spacepaint"
    borderless: bool = False
    fullscreen: bool = False
    vsync: bool = True
    development_mode: bool = False
    size: tuple[int, int] = (1280, 720)
    world_half_extent: float = 100.0
    camera_fov: float = 52.0
    # The 0.01-degree pitch is visually front-on while avoiding a Panda3D 1.10
    # fixed-pipeline culling edge case at an exact identity camera transform.
    camera_rotation: tuple[float, float, float] = (0.01, 0.0, 0.0)
    ship_camera_distance: float = 20.0
    ship_camera_min_distance: float = 1.0
    ship_camera_max_distance: float = 112.5
    ship_camera_rotation: tuple[float, float, float] = (12.0, 0.0, 0.0)
    ship_camera_follow_rate: float = 8.0
    artwork_camera_min_distance: float = 3.0
    artwork_camera_margin: float = 1.344
    artwork_camera_follow_rate: float = 5.0
    preview_seconds: float = 0.0
    enable_bloom: bool = True
    bloom_threshold: float = 0.56
    bloom_intensity: float = 1.35
    antialias_samples: int = 4
    enable_fxaa: bool = True
    show_nebula: bool = True
    show_stars: bool = True
    show_hud: bool = True
    axes_view: AxesView = AxesView.HIDDEN
    show_ship: bool = True
    show_beams: bool = True
    student_module: str = "student_code"

    def __post_init__(self) -> None:
        validate_multisamples(self.antialias_samples)
        if not isfinite(self.world_half_extent) or self.world_half_extent <= 0:
            raise ValueError("world_half_extent must be finite and greater than zero")
        if not isfinite(self.camera_fov) or not 0 < self.camera_fov < 180:
            raise ValueError(
                "camera_fov must be finite and between zero and 180 degrees"
            )
        if not isfinite(self.ship_camera_distance) or self.ship_camera_distance <= 0:
            raise ValueError(
                "ship_camera_distance must be finite and greater than zero"
            )
        if (
            not isfinite(self.ship_camera_min_distance)
            or self.ship_camera_min_distance <= 0
        ):
            raise ValueError(
                "ship_camera_min_distance must be finite and greater than zero"
            )
        if (
            not isfinite(self.ship_camera_max_distance)
            or self.ship_camera_max_distance <= self.ship_camera_min_distance
        ):
            raise ValueError(
                "ship_camera_max_distance must be finite and greater than "
                "ship_camera_min_distance"
            )
        if (
            not isfinite(self.ship_camera_follow_rate)
            or self.ship_camera_follow_rate <= 0
        ):
            raise ValueError(
                "ship_camera_follow_rate must be finite and greater than zero"
            )
        if (
            not isfinite(self.artwork_camera_min_distance)
            or self.artwork_camera_min_distance <= 0
        ):
            raise ValueError(
                "artwork_camera_min_distance must be finite and greater than zero"
            )
        if not isfinite(self.artwork_camera_margin) or self.artwork_camera_margin < 1:
            raise ValueError("artwork_camera_margin must be finite and at least one")
        if (
            not isfinite(self.artwork_camera_follow_rate)
            or self.artwork_camera_follow_rate <= 0
        ):
            raise ValueError(
                "artwork_camera_follow_rate must be finite and greater than zero"
            )


class RunnableApp(Protocol):
    def run(self) -> None:
        """Start the game loop."""

    def setBackgroundColor(
        self, red: float, green: float, blue: float, alpha: float = 1
    ) -> None:
        """Set the clear color."""

    def step(self) -> None:
        """Render one application frame."""

    def screenshot(
        self, namePrefix: PathLike[str], defaultFilename: bool = False
    ) -> PathLike[str] | None:
        """Write the current framebuffer to an image file."""

    def destroy(self) -> None:
        """Release the application and its graphics resources."""


class WindowLike(Protocol):
    title: str
    borderless: bool
    fullscreen: bool
    vsync: bool


@dataclass(frozen=True, slots=True)
class StudentProgramProblem:
    summary: str
    location: str


def configure_window(window: WindowLike, config: GameConfig) -> None:
    window.title = config.title
    window.borderless = config.borderless
    window.fullscreen = config.fullscreen
    window.vsync = config.vsync


def fps_text_for_delta(delta_seconds: float) -> str:
    if delta_seconds <= 0:
        return "--"
    return str(round(1 / delta_seconds))


def queue_step(queue: tuple[int, ...], direction: int) -> tuple[int, ...]:
    """Append a paused step, or cancel the most recent opposite step."""
    if direction not in (-1, 1):
        raise ValueError("step direction must be -1 or 1")
    if queue and queue[-1] == -direction:
        return queue[:-1]
    return queue + (direction,)


def axis_tick_values(half_extent: float) -> tuple[int, ...]:
    """Return each non-origin integer tick inside a centered axis extent."""
    if not isfinite(half_extent) or half_extent <= 0:
        raise ValueError("half_extent must be finite and greater than zero")
    outer_tick = int(half_extent)
    return tuple(
        tick
        for tick in range(-outer_tick, outer_tick + 1, AXIS_MINOR_TICK_INTERVAL)
        if tick != 0
    )


def axis_label_scale_for_distance(base_scale: float, distance: float) -> float:
    """Keep axis-label screen size stable using the original view calibration."""
    return base_scale * distance / AXIS_LABEL_REFERENCE_DISTANCE


def _student_problem(
    error: BaseException,
    module: ModuleType | None,
    fallback_filename: str = "student_code.py",
) -> StudentProgramProblem:
    filename = fallback_filename
    source_path: Path | None = None
    if module is not None and isinstance(getattr(module, "__file__", None), str):
        source_path = Path(cast(str, module.__file__)).resolve()
        filename = source_path.name
    line_number: int | None = None
    extracted = traceback.extract_tb(error.__traceback__)
    for frame in reversed(extracted):
        frame_path = Path(frame.filename).resolve()
        if (source_path is not None and frame_path == source_path) or (
            source_path is None and frame_path.name == filename
        ):
            line_number = frame.lineno
            break
    location = filename if line_number is None else f"{filename}:{line_number}"
    return StudentProgramProblem(f"{type(error).__name__}: {error}", location)


def _load_student_module(module_name: str) -> ModuleType:
    """Load a student module directly from the current working directory."""
    module_path = Path.cwd() / f"{module_name}.py"
    spec = spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load student program from {module_path}")

    module = module_from_spec(spec)
    previous_module = sys.modules.get(module_name)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if previous_module is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous_module
        raise
    return module


def load_student_program(
    module_name: str = "student_code",
    *,
    student_module: ModuleType | None = None,
) -> tuple[tuple[Command, ...], StudentProgramProblem | None]:
    """Record ``main`` from a supplied or named student module."""
    recorder = CommandRecorder()
    module = student_module
    fallback_filename = Path(f"{module_name}.py").name
    try:
        if module is None:
            module = _load_student_module(module_name)
        candidate = getattr(module, "main", None)
        if not callable(candidate):
            module_filename = (
                Path(cast(str, module.__file__)).name
                if isinstance(getattr(module, "__file__", None), str)
                else fallback_filename
            )
            raise TypeError(f"{module_filename} must define main(ship)")
        student_main = cast(Callable[[Ship], None], candidate)
        student_main(recorder)
    # Student programs may raise any ordinary exception; keep it visible in-app.
    except Exception as error:  # noqa: BLE001
        traceback.print_exc()
        return recorder.commands, _student_problem(error, module, fallback_filename)
    return recorder.commands, None


def _radial_texture(u: Any, tint: tuple[int, int, int, int], size: int = 96) -> Any:
    image = _panda.PNMImage(size, size, 4)
    center = (size - 1) / 2
    red, green, blue, opacity = tint
    for y in range(size):
        for x in range(size):
            dx = (x - center) / center
            dy = (y - center) / center
            radius = min(1.0, (dx * dx + dy * dy) ** 0.5)
            alpha = max(0.0, (1.0 - radius) ** 2.2) * opacity / 255
            image.setXelA(x, y, red / 255, green / 255, blue / 255, alpha)
    texture = _panda.Texture("spacepaint-radial")
    texture.load(image)
    texture.setMinfilter(_panda.SamplerState.FT_linear)
    texture.setMagfilter(_panda.SamplerState.FT_linear)
    return u.Texture(texture)


def _make_additive(entity: Any) -> None:
    blend = _panda.ColorBlendAttrib.make(
        _panda.ColorBlendAttrib.M_add,
        _panda.ColorBlendAttrib.O_incoming_alpha,
        _panda.ColorBlendAttrib.O_one,
    )
    entity.setAttrib(blend)
    entity.setDepthWrite(False)
    entity.setBin("transparent", 20)


def bounding_box_center(bounds: Bounds3) -> Point3:
    """Return the midpoint of an axis-aligned three-dimensional bounding box."""
    minimum, maximum = bounds
    return (
        (minimum[0] + maximum[0]) / 2,
        (minimum[1] + maximum[1]) / 2,
        (minimum[2] + maximum[2]) / 2,
    )


def camera_distance_for_bounding_box(
    bounds: Bounds3,
    vertical_fov: float,
    aspect_ratio: float,
    *,
    target: Point3 | None = None,
    margin: float = 1.0,
) -> float:
    """Return a rotation-independent distance that keeps ``bounds`` visible."""
    minimum, maximum = bounds
    if any(not isfinite(value) for point in bounds for value in point):
        raise ValueError("bounding box coordinates must be finite")
    if any(minimum[index] > maximum[index] for index in range(3)):
        raise ValueError("bounding box minimum must not exceed its maximum")
    if not isfinite(vertical_fov) or not 0 < vertical_fov < 180:
        raise ValueError("vertical_fov must be finite and between zero and 180 degrees")
    if not isfinite(aspect_ratio) or aspect_ratio <= 0:
        raise ValueError("aspect_ratio must be finite and greater than zero")
    if not isfinite(margin) or margin < 1:
        raise ValueError("margin must be finite and at least one")
    resolved_target = bounding_box_center(bounds) if target is None else target
    if any(not isfinite(value) for value in resolved_target):
        raise ValueError("camera target coordinates must be finite")
    radii = tuple(
        max(
            abs(minimum[index] - resolved_target[index]),
            abs(maximum[index] - resolved_target[index]),
        )
        for index in range(3)
    )
    radius = sqrt(sum(component * component for component in radii))
    if radius <= 1e-9:
        return 0.0
    vertical_half_fov = radians(vertical_fov) / 2
    horizontal_half_fov = atan(tan(vertical_half_fov) * aspect_ratio)
    limiting_half_fov = min(vertical_half_fov, horizontal_half_fov)
    return radius * margin / sin(limiting_half_fov)


def artwork_bounds(world: WorldState) -> Bounds3:
    """Bound the visible ship, beam aura geometry, and filled beam regions."""
    ship = world.pose.position
    minimum = [
        ship.x - ARTWORK_SHIP_BOUND_RADIUS,
        ship.y - ARTWORK_SHIP_BOUND_RADIUS,
        ship.z - ARTWORK_SHIP_BOUND_RADIUS,
    ]
    maximum = [
        ship.x + ARTWORK_SHIP_BOUND_RADIUS,
        ship.y + ARTWORK_SHIP_BOUND_RADIUS,
        ship.z + ARTWORK_SHIP_BOUND_RADIUS,
    ]

    def include(point: Vec3, padding: float = 0.0) -> None:
        coordinates = (point.x, point.y, point.z)
        for index, coordinate in enumerate(coordinates):
            minimum[index] = min(minimum[index], coordinate - padding)
            maximum[index] = max(maximum[index], coordinate + padding)

    for stroke in world.strokes:
        padding = stroke.style.width * ARTWORK_BEAM_AURA_HALF_WIDTH_SCALE
        for sample in stroke.samples:
            include(sample.position, padding)
    for region in world.fills:
        for vertex in region.vertices:
            include(vertex)
    return (
        (minimum[0], minimum[1], minimum[2]),
        (maximum[0], maximum[1], maximum[2]),
    )


class OriginOrbitCamera:
    """Automatically frame the artwork or follow the ship."""

    def __init__(self, u: Any, config: GameConfig) -> None:
        self._u = u
        self.target = u.Entity(position=(0, 0, 0))
        self.pivot = u.Entity(parent=self.target, position=(0, 0, 0))
        u.camera.parent = self.pivot
        u.camera.fov = config.camera_fov
        self._vertical_fov = config.camera_fov
        self._ship_initial_distance = config.ship_camera_distance
        self._ship_distance = self._clamp_distance(
            config.ship_camera_distance,
            config.ship_camera_min_distance,
            config.ship_camera_max_distance,
        )
        self._ship_min_distance = config.ship_camera_min_distance
        self._ship_max_distance = config.ship_camera_max_distance
        self._ship_initial_rotation = config.ship_camera_rotation
        self._ship_rotation = config.ship_camera_rotation
        self._ship_follow_rate = config.ship_camera_follow_rate
        self._ship_follow_position = (0.0, 0.0, 0.0)
        self._artwork_initial_rotation = config.camera_rotation
        self._artwork_rotation = config.camera_rotation
        self._artwork_min_distance = config.artwork_camera_min_distance
        self._artwork_margin = config.artwork_camera_margin
        self._artwork_follow_rate = config.artwork_camera_follow_rate
        radius = ARTWORK_SHIP_BOUND_RADIUS
        self._artwork_bounds: Bounds3 = (
            (-radius, -radius, -radius),
            (radius, radius, radius),
        )
        self._artwork_aspect_ratio = 16 / 9
        self._artwork_follow_position = (0.0, 0.0, 0.0)
        self._artwork_zoom_factor = 1.0
        self._artwork_distance = self._artwork_required_distance(
            self._artwork_follow_position
        )
        self._view = CameraView.ART
        self.reset()

    @staticmethod
    def _clamp_distance(distance: float, minimum: float, maximum: float) -> float:
        return max(minimum, min(maximum, distance))

    @property
    def maximum_distance(self) -> float:
        return self._ship_max_distance

    @property
    def distance(self) -> float:
        if self._view is CameraView.SHIP:
            return self._ship_distance
        return self._artwork_distance

    @property
    def view(self) -> CameraView:
        return self._view

    @property
    def ship_view_enabled(self) -> bool:
        return self._view is CameraView.SHIP

    @property
    def artwork_view_enabled(self) -> bool:
        return self._view is CameraView.ART

    def _active_rotation(self) -> tuple[float, float, float]:
        if self._view is CameraView.SHIP:
            return self._ship_rotation
        return self._artwork_rotation

    def _active_limits(self) -> tuple[float, float]:
        if self._view is CameraView.SHIP:
            return self._ship_min_distance, self._ship_max_distance
        return self._artwork_min_distance, float("inf")

    def _set_active_distance(self, distance: float) -> None:
        minimum, maximum = self._active_limits()
        clamped = self._clamp_distance(distance, minimum, maximum)
        if self._view is CameraView.SHIP:
            self._ship_distance = clamped
        else:
            self._artwork_distance = clamped

    def _set_active_rotation(self, rotation: tuple[float, float, float]) -> None:
        if self._view is CameraView.SHIP:
            self._ship_rotation = rotation
        else:
            self._artwork_rotation = rotation

    def _apply_active_view(self) -> None:
        self.pivot.rotation = self._active_rotation()
        self._u.camera.position = (0, 0, self.distance)

    def _set_ship_target(
        self,
        position: tuple[float, float, float],
        orientation: Quaternion,
    ) -> None:
        self._ship_follow_position = position
        self.target.position = position
        self.target.setQuat(
            _panda.Quat(
                orientation.w,
                orientation.x,
                orientation.y,
                orientation.z,
            )
        )

    def _set_unrotated_target(self, position: Point3) -> None:
        self.target.position = position
        self.target.rotation = (0, 0, 0)

    def _artwork_required_distance(self, target: Point3) -> float:
        fitted = camera_distance_for_bounding_box(
            self._artwork_bounds,
            self._vertical_fov,
            self._artwork_aspect_ratio,
            target=target,
            margin=self._artwork_margin,
        )
        return max(
            self._artwork_min_distance,
            fitted * self._artwork_zoom_factor,
        )

    def _enter_artwork_view(
        self,
        bounds: Bounds3,
        aspect_ratio: float,
    ) -> None:
        self._artwork_bounds = bounds
        self._artwork_aspect_ratio = aspect_ratio
        self._artwork_follow_position = bounding_box_center(bounds)
        self._artwork_distance = self._artwork_required_distance(
            self._artwork_follow_position
        )
        self._set_unrotated_target(self._artwork_follow_position)

    def frame_artwork(self, bounds: Bounds3, aspect_ratio: float) -> None:
        """Restore the default artwork view and fit the supplied bounds exactly."""
        self._view = CameraView.ART
        self._artwork_rotation = self._artwork_initial_rotation
        self._artwork_zoom_factor = 1.0
        self._enter_artwork_view(bounds, aspect_ratio)
        self.reset()

    def cycle_view(
        self,
        position: tuple[float, float, float],
        orientation: Quaternion,
        bounds: Bounds3,
        aspect_ratio: float,
    ) -> None:
        if self._view is CameraView.SHIP:
            self._view = CameraView.ART
            self._enter_artwork_view(bounds, aspect_ratio)
        else:
            self._view = CameraView.SHIP
            self._set_ship_target(position, orientation)
        self._apply_active_view()

    def reset(self) -> None:
        if self._view is CameraView.SHIP:
            self._ship_rotation = self._ship_initial_rotation
            self._ship_distance = self._clamp_distance(
                self._ship_initial_distance,
                self._ship_min_distance,
                self._ship_max_distance,
            )
        else:
            self._artwork_rotation = self._artwork_initial_rotation
            self._artwork_zoom_factor = 1.0
            self._artwork_follow_position = bounding_box_center(self._artwork_bounds)
            self._artwork_distance = self._artwork_required_distance(
                self._artwork_follow_position
            )
            self._set_unrotated_target(self._artwork_follow_position)
        self._apply_active_view()
        self._u.camera.rotation = (0, 180, 0)
        # Looking back from +Z reverses Ursina's camera-right direction. Mirror
        # the view so the documented student axes remain +X right and +Y up.
        self._u.camera.scale_x = -1

    def update(
        self,
        ship_position: tuple[float, float, float] | None = None,
        ship_orientation: Quaternion | None = None,
        art_bounds: Bounds3 | None = None,
        aspect_ratio: float | None = None,
    ) -> None:
        if (
            self._view is CameraView.SHIP
            and ship_position is not None
            and ship_orientation is not None
        ):
            amount = 1.0 - exp(
                -self._ship_follow_rate * max(0.0, float(self._u.time.dt))
            )
            current_x, current_y, current_z = self._ship_follow_position
            target_x, target_y, target_z = ship_position
            followed_position = (
                current_x + (target_x - current_x) * amount,
                current_y + (target_y - current_y) * amount,
                current_z + (target_z - current_z) * amount,
            )
            self._set_ship_target(followed_position, ship_orientation)
        elif (
            self._view is CameraView.ART
            and art_bounds is not None
            and aspect_ratio is not None
        ):
            self._artwork_bounds = art_bounds
            self._artwork_aspect_ratio = aspect_ratio
            target_position = bounding_box_center(art_bounds)
            amount = 1.0 - exp(
                -self._artwork_follow_rate * max(0.0, float(self._u.time.dt))
            )
            current_x, current_y, current_z = self._artwork_follow_position
            target_x, target_y, target_z = target_position
            self._artwork_follow_position = (
                current_x + (target_x - current_x) * amount,
                current_y + (target_y - current_y) * amount,
                current_z + (target_z - current_z) * amount,
            )
            self._set_unrotated_target(self._artwork_follow_position)
            required_distance = self._artwork_required_distance(
                self._artwork_follow_position
            )
            if required_distance >= self._artwork_distance:
                self._artwork_distance = required_distance
            else:
                self._artwork_distance += (
                    required_distance - self._artwork_distance
                ) * amount
            self._u.camera.z = self._artwork_distance
        if self._u.held_keys["left mouse"]:
            velocity = self._u.mouse.velocity
            pitch, yaw, roll = self._active_rotation()
            yaw -= float(velocity.x) * 150
            pitch = max(-82, min(82, pitch + float(velocity.y) * 150))
            self._set_active_rotation((pitch, yaw, roll))
            self.pivot.rotation = self._active_rotation()

    def input(self, key: str) -> None:
        if key == "scroll up":
            if self._view is CameraView.ART:
                self._artwork_zoom_factor *= 0.88
            self._set_active_distance(self.distance * 0.88)
            self._u.camera.z = self.distance
        elif key == "scroll down":
            if self._view is CameraView.ART:
                self._artwork_zoom_factor *= 1.12
            self._set_active_distance(self.distance * 1.12)
            self._u.camera.z = self.distance
        elif key == "0":
            self.reset()


class SpacepaintScene:
    """Projection of pure WorldState into Ursina entities."""

    def __init__(
        self,
        u: Any,
        config: GameConfig,
        commands: tuple[Command, ...],
        problem: StudentProgramProblem | None,
    ) -> None:
        self.u = u
        self.config = config
        self.commands = commands
        self.problem = problem
        self.world = initial_world_state()
        self.playback_rate = 1.0
        self.step_queue: tuple[int, ...] = ()
        self._step_direction: int | None = None
        self._step_target: int | None = None
        self._rewind_base: WorldState | None = None
        self._rewind_stop_index: int | None = None
        self._rewind_duration = 0.0
        self._rewind_elapsed = 0.0
        self.hud_visible = config.show_hud
        self.axes_view = config.axes_view
        self.camera = OriginOrbitCamera(u, config)
        self._bloom: Any | None = None

        self._build_background()
        self._build_axes()
        self._build_ship()
        self._build_beams()
        self._build_hud()
        self._enable_bloom()

        if config.preview_seconds > 0:
            self.world = advance(self.world, self.commands, config.preview_seconds)
        self._project_world()

        updater = u.Entity(eternal=True, ignore_paused=True)
        updater.update = self.update
        updater.input = self.input
        updater.on_destroy = self.cleanup
        self._updater = updater

    def _colored_entity(self, color_value: Any, **kwargs: Any) -> Any:
        """Create an entity whose flat color survives parented fixed-pipeline rendering."""
        entity = self.u.Entity(**kwargs)
        if entity.model:
            entity.model.setColor(color_value)
        return entity

    def _build_background(self) -> None:
        u = self.u
        extent = self.config.world_half_extent
        world_corner_radius = extent * sqrt(3)
        self._colored_entity(
            u.color.rgb32(12, 7, 29),
            model="sphere",
            scale=max(
                76.0,
                max(self.camera.maximum_distance, world_corner_radius)
                * BACKGROUND_SPHERE_SCALE_MARGIN,
            ),
            double_sided=True,
            unlit=True,
        )
        nebulae = (
            (
                (-0.56 * extent, 0.33 * extent, -0.72 * extent),
                (0.56 * extent, 0.33 * extent),
                (116, 42, 105, 92),
                -16,
            ),
            (
                (0.51 * extent, -0.37 * extent, -0.57 * extent),
                (0.61 * extent, 0.37 * extent),
                (181, 62, 55, 72),
                21,
            ),
            (
                (0.05 * extent, 0.56 * extent, -0.80 * extent),
                (0.48 * extent, 0.24 * extent),
                (62, 70, 159, 58),
                7,
            ),
            (
                (-0.64 * extent, -0.51 * extent, -0.40 * extent),
                (0.43 * extent, 0.32 * extent),
                (224, 112, 60, 42),
                -28,
            ),
            (
                (0.61 * extent, 0.51 * extent, 0.13 * extent),
                (0.45 * extent, 0.29 * extent),
                (78, 111, 209, 48),
                13,
            ),
        )
        if self.config.show_nebula:
            for position, scale, tint, rotation in nebulae:
                radial = _radial_texture(u, tint)
                cloud = self._colored_entity(
                    u.color.white,
                    model="quad",
                    texture=radial,
                    position=position,
                    scale=scale,
                    rotation_z=rotation,
                    double_sided=True,
                    billboard=True,
                )
                _make_additive(cloud)

        random = Random(110)
        star_layers = ((2.0, 900), (4.0, 180)) if self.config.show_stars else ()
        for thickness, count in star_layers:
            vertices: list[Any] = []
            for _ in range(count):
                x = random.uniform(-extent, extent)
                y = random.uniform(-extent, extent)
                z = random.uniform(-extent, extent)
                vertices.append(u.Vec3(x, y, z))
            star_mesh = u.Mesh(
                vertices=vertices,
                mode="point",
                thickness=thickness,
                render_points_in_3d=False,
            )
            star_color = (
                u.color.rgba32(178, 211, 255, 185)
                if thickness < 3
                else u.color.rgba32(255, 215, 177, 225)
            )
            stars = self._colored_entity(star_color, model=star_mesh, unlit=True)
            _make_additive(stars)

    def _build_ship(self) -> None:
        u = self.u
        root = u.Entity(position=(0, 0, 0), scale=0.72)
        self.ship_root = root
        self.ship_root.enabled = self.config.show_ship

        nose_vertices = (
            u.Vec3(0.95, 0, 0),
            u.Vec3(0.12, 0.28, 0.20),
            u.Vec3(0.12, -0.28, 0.20),
            u.Vec3(0.12, -0.28, -0.20),
            u.Vec3(0.12, 0.28, -0.20),
        )
        nose_triangles = (
            0,
            1,
            2,
            0,
            2,
            3,
            0,
            3,
            4,
            0,
            4,
            1,
            1,
            4,
            3,
            1,
            3,
            2,
        )
        self._colored_entity(
            u.color.rgb32(58, 78, 112),
            parent=root,
            model=u.Mesh(vertices=nose_vertices, triangles=nose_triangles),
            unlit=True,
        )
        self._colored_entity(
            u.color.rgb32(31, 43, 70),
            parent=root,
            model="cube",
            position=(-0.34, 0, 0),
            scale=(0.92, 0.42, 0.38),
            unlit=True,
        )
        for side in (-1, 1):
            self._colored_entity(
                u.color.rgb32(40, 55, 86),
                parent=root,
                model="cube",
                position=(-0.18, side * 0.36, 0.01),
                scale=(0.90, 0.36, 0.075),
                rotation_z=-side * 13,
                unlit=True,
            )
            self._colored_entity(
                u.color.rgb32(20, 29, 52),
                parent=root,
                model="cube",
                position=(-0.46, side * 0.56, 0.0),
                scale=(0.34, 0.12, 0.14),
                unlit=True,
            )
            self._colored_entity(
                u.color.rgba32(92, 226, 255, 230),
                parent=root,
                model="sphere",
                position=(-0.79, side * 0.16, 0),
                scale=(0.14, 0.11, 0.11),
                unlit=True,
            )

        canopy = self._colored_entity(
            u.color.rgba32(57, 215, 255, 220),
            parent=root,
            model="sphere",
            position=(0.26, 0, 0.15),
            scale=(0.43, 0.18, 0.18),
            unlit=True,
        )
        _make_additive(canopy)
        self._colored_entity(
            u.color.rgb32(255, 137, 69),
            parent=root,
            model="cube",
            position=(-0.18, 0, 0.22),
            scale=(0.65, 0.055, 0.035),
            unlit=True,
        )

        self.exhaust_particles: list[Any] = []
        for index in range(12):
            particle = self._colored_entity(
                u.color.rgba32(91, 227, 255, 180),
                parent=root,
                model="sphere",
                scale=0.045,
                unlit=True,
            )
            particle.phase = index / 12
            self.exhaust_particles.append(particle)
            _make_additive(particle)

        self.beam_head = self._colored_entity(
            u.color.rgba32(80, 235, 255, 210),
            model="sphere",
            scale=0.20,
        )
        _make_additive(self.beam_head)

    def _axis_line_mesh(
        self,
        segments: list[
            tuple[
                tuple[float, float, float],
                tuple[float, float, float],
            ]
        ],
        thickness: float,
    ) -> Any:
        vertices: list[tuple[float, float, float]] = []
        line_indices: list[tuple[int, int]] = []
        for start, end in segments:
            index = len(vertices)
            vertices.extend((start, end))
            line_indices.append((index, index + 1))
        return self.u.Mesh(
            vertices=vertices,
            triangles=line_indices,
            mode="line",
            thickness=thickness,
        )

    def _build_axes(self) -> None:
        u = self.u
        extent = self.config.world_half_extent
        self.axes_root = u.Entity()
        self.xy_axes_root = u.Entity(parent=self.axes_root)
        self.z_axis_root = u.Entity(parent=self.axes_root)
        self._apply_axes_view()
        self.axis_labels: list[
            tuple[
                Any,
                tuple[float, float, float],
                tuple[float, float, float] | None,
                float,
            ]
        ] = []
        directions = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
        perpendiculars = (
            ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
            ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
            ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        )
        label_offsets = ((0.0, -1.2, -0.4), (-1.35, 0.0, -0.4), (1.15, 0.75, 0.0))
        axis_colors = (
            u.color.rgba32(235, 80, 94, 230),
            u.color.rgba32(70, 214, 128, 230),
            u.color.rgba32(82, 153, 235, 230),
        )
        tick_values = axis_tick_values(extent)

        # Keep names near the origin and midway between the 10- and 15-unit
        # labels so they remain distinct from numbered major ticks.
        name_distance = min(extent, AXIS_NAME_DISTANCE)

        for axis_index, (axis_name, direction, color_value) in enumerate(
            zip(("X", "Y", "Z"), directions, axis_colors, strict=True)
        ):
            axis_parent = self.xy_axes_root if axis_index < 2 else self.z_axis_root
            start = (
                -extent * direction[0],
                -extent * direction[1],
                -extent * direction[2],
            )
            end = (
                extent * direction[0],
                extent * direction[1],
                extent * direction[2],
            )
            axis_mesh = self._axis_line_mesh([(start, end)], 2.2)
            self._colored_entity(
                color_value,
                parent=axis_parent,
                model=axis_mesh,
                unlit=True,
            )

            minor_segments: list[
                tuple[tuple[float, float, float], tuple[float, float, float]]
            ] = []
            major_segments: list[
                tuple[tuple[float, float, float], tuple[float, float, float]]
            ] = []
            for tick in tick_values:
                is_major = tick % AXIS_MAJOR_TICK_INTERVAL == 0
                radius = 0.42 if is_major else 0.20
                segments = major_segments if is_major else minor_segments
                center = (
                    tick * direction[0],
                    tick * direction[1],
                    tick * direction[2],
                )
                for perpendicular in perpendiculars[axis_index]:
                    segments.append(
                        (
                            (
                                center[0] - radius * perpendicular[0],
                                center[1] - radius * perpendicular[1],
                                center[2] - radius * perpendicular[2],
                            ),
                            (
                                center[0] + radius * perpendicular[0],
                                center[1] + radius * perpendicular[1],
                                center[2] + radius * perpendicular[2],
                            ),
                        )
                    )

                if is_major:
                    offset = label_offsets[axis_index]
                    label_position = (
                        center[0] + offset[0],
                        center[1] + offset[1],
                        center[2] + offset[2],
                    )
                    label = u.Text(
                        parent=axis_parent,
                        text=str(tick),
                        position=label_position,
                        origin=(0, 0),
                        scale=(-AXIS_TICK_LABEL_SCALE, AXIS_TICK_LABEL_SCALE),
                        color=color_value,
                        billboard=True,
                        double_sided=True,
                    )
                    self.axis_labels.append(
                        (label, label_position, direction, AXIS_TICK_LABEL_SCALE)
                    )

            for segments, thickness in ((minor_segments, 1.0), (major_segments, 2.0)):
                tick_mesh = self._axis_line_mesh(segments, thickness)
                self._colored_entity(
                    color_value,
                    parent=axis_parent,
                    model=tick_mesh,
                    unlit=True,
                )

            name_position = (
                name_distance * direction[0],
                name_distance * direction[1],
                name_distance * direction[2],
            )
            name_offset = label_offsets[axis_index]
            name_label_position = (
                name_position[0] + 1.8 * name_offset[0],
                name_position[1] + 1.8 * name_offset[1],
                name_position[2] + 1.8 * name_offset[2],
            )
            name_label = u.Text(
                parent=axis_parent,
                text=axis_name,
                position=name_label_position,
                origin=(0, 0),
                scale=(-AXIS_NAME_LABEL_SCALE, AXIS_NAME_LABEL_SCALE),
                color=color_value,
                billboard=True,
                double_sided=True,
            )
            self.axis_labels.append(
                (name_label, name_label_position, None, AXIS_NAME_LABEL_SCALE)
            )

        origin_label_position = (0.65, -0.7, 0.0)
        origin_label = u.Text(
            parent=self.xy_axes_root,
            text="0",
            position=origin_label_position,
            origin=(0, 0),
            scale=(-AXIS_TICK_LABEL_SCALE, AXIS_TICK_LABEL_SCALE),
            color=u.color.rgba32(205, 218, 235, 230),
            billboard=True,
            double_sided=True,
        )
        self.axis_labels.append(
            (origin_label, origin_label_position, None, AXIS_TICK_LABEL_SCALE)
        )

    def _update_axis_labels(self) -> None:
        if self.axes_view is AxesView.HIDDEN:
            return
        camera_position = self.u.camera.world_position
        camera_forward = self.u.camera.forward
        for label, position, axis_direction, base_scale in self.axis_labels:
            offset = self.u.Vec3(*position) - camera_position
            in_front_of_camera = float(offset.dot(camera_forward)) > 0.1
            is_foreshortened = (
                axis_direction is not None
                and abs(float(self.u.Vec3(*axis_direction).dot(camera_forward))) > 0.94
            )
            label.enabled = in_front_of_camera and not is_foreshortened
            distance = max(0.1, float(offset.length()))
            scale = axis_label_scale_for_distance(base_scale, distance)
            # The world camera is mirrored horizontally to keep student +X on
            # screen-right. Negating only local X keeps billboard text upright
            # while restoring its normal left-to-right glyph orientation.
            label.scale = (-scale, scale)

    def _empty_mesh(self) -> Any:
        return self.u.Mesh(vertices=[], triangles=[], static=False, mode="triangle")

    def _build_beams(self) -> None:
        self.trail_batches: list[tuple[Any, Any, Any, Any, Any, Any]] = []
        self.trail_batch_styles: tuple[object, ...] = ()
        self.fill_batches: list[tuple[Any, Any]] = []
        self.fill_batch_colors: tuple[object, ...] = ()

    def _build_hud(self) -> None:
        u = self.u
        self.hud_root = u.Entity(parent=u.camera.ui)
        self.hud_root.enabled = self.config.show_hud
        self.status_text = u.Text(
            parent=self.hud_root,
            text="",
            position=(-0.86, 0.45),
            origin=(-0.5, 0.5),
            scale=0.78,
            color=u.color.rgb32(206, 236, 255),
            background=False,
        )
        self.controls_text = u.Text(
            parent=self.hud_root,
            text=(
                "SPACE pause   LEFT slower / RIGHT faster (paused: step)   R replay   "
                "A axes   V view   0 camera   H hide   drag orbit   scroll zoom"
            ),
            position=(-0.86, -0.46),
            origin=(-0.5, -0.5),
            scale=0.62,
            color=u.color.rgba32(170, 204, 235, 210),
            background=False,
        )
        self.axes_button = u.Button(
            parent=self.hud_root,
            text=f"A  AXES {self.axes_view.value}",
            position=(0.76, -0.43),
            scale=(0.17, 0.055),
            color=u.color.rgba32(31, 50, 78, 235),
            text_color=u.color.rgb32(206, 236, 255),
            text_size=0.72,
            radius=0.15,
            on_click=self.cycle_axes,
        )
        self._update_axes_button()
        self.camera_button = u.Button(
            parent=self.hud_root,
            text="V  ART VIEW",
            position=(0.56, -0.43),
            scale=(0.19, 0.055),
            color=u.color.rgba32(31, 50, 78, 235),
            text_color=u.color.rgb32(206, 236, 255),
            text_size=0.72,
            radius=0.15,
            on_click=self.toggle_camera_view,
        )
        self._update_camera_button()
        self.error_text = u.Text(
            parent=self.hud_root,
            text="",
            position=(-0.72, 0.12),
            origin=(-0.5, 0.5),
            scale=0.85,
            color=u.color.rgb32(255, 190, 178),
            background=False,
        )
        if self.problem is not None:
            self.error_text.text = (
                "STUDENT PROGRAM ERROR\n"
                f"{self.problem.location}\n"
                f"{self.problem.summary}\n"
                "Fix the program and restart Spacepaint."
            )
            self.error_text.create_background()

    def _update_axes_button(self) -> None:
        self.axes_button.text = f"A  AXES {self.axes_view.value}"

    def _apply_axes_view(self) -> None:
        axes_shown = self.axes_view is not AxesView.HIDDEN
        self.axes_root.enabled = axes_shown
        self.xy_axes_root.enabled = axes_shown
        self.z_axis_root.enabled = self.axes_view is AxesView.XYZ

    def cycle_axes(self) -> None:
        self.axes_view = {
            AxesView.HIDDEN: AxesView.XY,
            AxesView.XY: AxesView.XYZ,
            AxesView.XYZ: AxesView.HIDDEN,
        }[self.axes_view]
        self._apply_axes_view()
        self._update_axes_button()

    def _update_camera_button(self) -> None:
        state = self.camera.view.value
        self.camera_button.text = f"V  {state} VIEW"

    def toggle_camera_view(self) -> None:
        pose = self.world.pose
        position = pose.position
        self.camera.cycle_view(
            (position.x, position.y, position.z),
            pose.orientation,
            artwork_bounds(self.world),
            float(self.u.window.aspect_ratio),
        )
        self._update_camera_button()

    def _enable_bloom(self) -> None:
        if not self.config.enable_bloom:
            return
        try:
            showbase_globals = cast(
                Any, import_module("direct.showbase.ShowBaseGlobal")
            )
            if prefers_native_bloom(sys.platform):
                self._bloom = NativeBloomPipeline.create(
                    showbase_globals.base,
                    NativeBloomConfig(
                        threshold=self.config.bloom_threshold,
                        intensity=self.config.bloom_intensity,
                        antialias_samples=self.config.antialias_samples,
                        enable_fxaa=self.config.enable_fxaa,
                    ),
                )
                print(
                    "Spacepaint: native GLSL 120 bloom enabled "
                    f"({self.config.antialias_samples}x MSAA, "
                    f"FXAA {'on' if self.config.enable_fxaa else 'off'})"
                )
                return

            filters_module = cast(Any, import_module("direct.filter.CommonFilters"))
            filters = filters_module.CommonFilters(
                showbase_globals.base.win, showbase_globals.base.cam
            )
            if self.config.antialias_samples > 0:
                filters.setMSAA(self.config.antialias_samples)
            enabled = bool(
                filters.setBloom(
                    blend=(0.28, 0.36, 0.30, 0.0),
                    mintrigger=0.52,
                    maxtrigger=1.0,
                    desat=0.2,
                    intensity=1.25,
                    size="small",
                )
            )
            if enabled:
                self._bloom = filters
        # Graphics backends can fail with backend-specific exception types.
        except Exception as error:  # noqa: BLE001
            print(
                f"Spacepaint: bloom unavailable; using layered beam fallback ({error})"
            )

    def cleanup(self) -> None:
        bloom = self._bloom
        self._bloom = None
        if bloom is not None and hasattr(bloom, "cleanup"):
            with suppress(Exception):
                bloom.cleanup()

    def _update_mesh(self, mesh: Any, data: TrailMeshData | FillMeshData) -> None:
        signature = (data.vertices, data.triangles)
        if getattr(mesh, "spacepaint_signature", None) == signature:
            return
        u = self.u
        mesh.vertices = [
            u.Vec3(vertex.x, vertex.y, vertex.z) for vertex in data.vertices
        ]
        mesh.triangles = list(data.triangles)
        mesh.colors = []
        mesh.generate()
        mesh.spacepaint_signature = signature

    def _rebuild_fill_batches(self, regions: tuple[FillRegion, ...]) -> None:
        for _, entity in self.fill_batches:
            self.u.destroy(entity)
        self.fill_batches = []
        for _ in regions:
            mesh = self._empty_mesh()
            entity = self.u.Entity(
                model=mesh,
                double_sided=True,
                transparency=True,
                unlit=True,
            )
            entity.setDepthWrite(False)
            entity.setBin("transparent", 10)
            self.fill_batches.append((mesh, entity))
        self.fill_batch_colors = tuple(region.color for region in regions)

    def _update_fills(self) -> None:
        regions = self.world.fills
        colors = tuple(region.color for region in regions)
        if colors != self.fill_batch_colors:
            self._rebuild_fill_batches(regions)
        for region, (mesh, entity) in zip(regions, self.fill_batches, strict=True):
            self._update_mesh(mesh, build_fill_mesh(region))
            fill_color = self.u.color.rgba32(*fill_rgba32(region))
            entity.color = fill_color
            entity.model.setColor(fill_color)

    def _rebuild_trail_batches(self, strokes: tuple[BeamStroke, ...]) -> None:
        for batch in self.trail_batches:
            for entity in (batch[1], batch[3], batch[5]):
                self.u.destroy(entity)
        self.trail_batches = []
        for _ in strokes:
            core_mesh = self._empty_mesh()
            halo_mesh = self._empty_mesh()
            aura_mesh = self._empty_mesh()
            core_entity = self.u.Entity(
                model=core_mesh, double_sided=True, transparency=True
            )
            halo_entity = self.u.Entity(
                model=halo_mesh, double_sided=True, transparency=True
            )
            aura_entity = self.u.Entity(
                model=aura_mesh, double_sided=True, transparency=True
            )
            _make_additive(halo_entity)
            _make_additive(aura_entity)
            self.trail_batches.append(
                (core_mesh, core_entity, halo_mesh, halo_entity, aura_mesh, aura_entity)
            )
        self.trail_batch_styles = tuple(stroke.style for stroke in strokes)

    def _update_trails(self) -> None:
        strokes = self.world.strokes
        now = self.world.elapsed_time
        styles = tuple(stroke.style for stroke in strokes)
        if styles != self.trail_batch_styles:
            self._rebuild_trail_batches(strokes)
        for stroke, batch in zip(strokes, self.trail_batches, strict=True):
            core_mesh, core_entity, halo_mesh, halo_entity, aura_mesh, aura_entity = (
                batch
            )
            core = build_trail_mesh((stroke,), now, width_scale=0.32)
            halo = build_trail_mesh((stroke,), now, width_scale=1.8)
            aura = build_trail_mesh((stroke,), now, width_scale=3.8)
            self._update_mesh(core_mesh, core)
            self._update_mesh(halo_mesh, halo)
            self._update_mesh(aura_mesh, aura)
            alpha = max(
                (
                    beam_sample_alpha(sample, stroke.style, now)
                    for sample in stroke.samples
                ),
                default=0.0,
            )
            red, green, blue = stroke.style.color
            core_color = self.u.color.rgba32(
                round((red + (1 - red) * 0.72) * 255),
                round((green + (1 - green) * 0.72) * 255),
                round((blue + (1 - blue) * 0.72) * 255),
                round(245 * alpha),
            )
            halo_color = self.u.color.rgba32(
                round((red + (1 - red) * 0.18) * 255),
                round((green + (1 - green) * 0.18) * 255),
                round((blue + (1 - blue) * 0.18) * 255),
                round(66 * alpha),
            )
            aura_color = self.u.color.rgba32(
                round(red * 255),
                round(green * 255),
                round(blue * 255),
                round(23 * alpha),
            )
            for entity, color_value in (
                (core_entity, core_color),
                (halo_entity, halo_color),
                (aura_entity, aura_color),
            ):
                entity.color = color_value
                entity.model.setColor(color_value)

    def _clear_active_step(self) -> None:
        self._step_direction = None
        self._step_target = None
        self._rewind_base = None
        self._rewind_stop_index = None
        self._rewind_duration = 0.0
        self._rewind_elapsed = 0.0

    def _start_next_step(self) -> None:
        if (
            self._step_direction is not None
            or not self.world.paused
            or not self.step_queue
        ):
            return
        direction = self.step_queue[0]
        self.step_queue = self.step_queue[1:]
        if direction > 0:
            if self.world.command_index >= len(self.commands):
                return
            self._step_direction = 1
            self._step_target = self.world.command_index + 1
            self.world = set_paused(self.world, False)
            return

        if self.world.active_motion is not None:
            target_index = self.world.command_index
            stop_index = min(len(self.commands), target_index + 1)
            source = replace(self.world, paused=False)
        else:
            stop_index = self.world.command_index
            if stop_index <= 0:
                return
            target_index = stop_index - 1
            source = replay_to_command(self.commands, stop_index)
        base = replay_to_command(self.commands, target_index)
        duration = max(
            0.0, (source.elapsed_time - base.elapsed_time) * base.speed_multiplier
        )
        if duration <= 1e-9:
            self.world = set_paused(base, True)
            return
        self._step_direction = -1
        self._rewind_base = base
        self._rewind_stop_index = stop_index
        self._rewind_duration = duration
        self._rewind_elapsed = 0.0

    def _advance_forward_step(self, delta_seconds: float) -> None:
        target = self._step_target
        if target is None:
            self._clear_active_step()
            return
        step_delta = delta_seconds / self.world.speed_multiplier
        self.world = advance(
            self.world,
            self.commands,
            step_delta,
            stop_before_command_index=target,
        )
        finished = (
            self.world.command_index >= target and self.world.active_motion is None
        )
        if not finished and not self.world.paused:
            return
        breakpoint_command = self.commands[target - 1]
        hit_speed_zero = (
            isinstance(breakpoint_command, SetSpeedCommand)
            and breakpoint_command.multiplier == 0
        )
        self.world = set_paused(self.world, True)
        self._clear_active_step()
        if hit_speed_zero:
            self.step_queue = ()

    def _advance_backward_step(self, delta_seconds: float) -> None:
        base = self._rewind_base
        stop_index = self._rewind_stop_index
        if base is None or stop_index is None:
            self._clear_active_step()
            return
        self._rewind_elapsed = min(
            self._rewind_duration,
            self._rewind_elapsed + delta_seconds,
        )
        remaining = self._rewind_duration - self._rewind_elapsed
        if remaining <= 1e-9:
            self.world = set_paused(base, True)
            self._clear_active_step()
            return
        sample = advance(
            base,
            self.commands,
            remaining / base.speed_multiplier,
            stop_before_command_index=stop_index,
        )
        self.world = set_paused(sample, True)

    def _project_world(self) -> None:
        pose = self.world.pose
        position = pose.position
        orientation: Quaternion = pose.orientation
        self.ship_root.position = (position.x, position.y, position.z)
        self.ship_root.setQuat(
            _panda.Quat(orientation.w, orientation.x, orientation.y, orientation.z)
        )

        style = self.world.beam_style
        red, green, blue = style.color
        self.beam_head.position = (position.x, position.y, position.z)
        self.beam_head.scale = max(0.10, style.width * 1.7)
        head_color = self.u.color.rgba32(
            round(red * 255), round(green * 255), round(blue * 255), 205
        )
        self.beam_head.color = head_color
        self.beam_head.model.setColor(head_color)
        self.beam_head.enabled = self.config.show_beams and self.world.beam_enabled

        for index, particle in enumerate(self.exhaust_particles):
            phase = (self.world.elapsed_time * 1.9 + float(particle.phase)) % 1.0
            particle.x = -0.78 - phase * 0.62
            particle.y = (0.16 if index % 2 == 0 else -0.16) + (phase - 0.5) * 0.035
            particle.z = (index % 3 - 1) * 0.025
            particle.scale = 0.065 * (1.0 - phase * 0.75)
            particle_color = self.u.color.rgba32(
                91, 227, 255, round(180 * (1.0 - phase))
            )
            particle.color = particle_color
            particle.model.setColor(particle_color)

        if self.config.show_beams:
            self._update_fills()
            self._update_trails()
        if self._step_direction is not None:
            status = f"STEPPING {'RIGHT' if self._step_direction > 0 else 'LEFT'}"
        else:
            status = (
                "PAUSED"
                if self.world.paused
                else ("COMPLETE" if self.world.completed else "PLAYING")
            )
        total = len(self.commands)
        current = min(self.world.command_index + 1, total) if total else 0
        fade = (
            "permanent" if style.fade_after is None else f"fade {style.fade_after:g}s"
        )
        active_steps = () if self._step_direction is None else (self._step_direction,)
        queued_steps = active_steps + self.step_queue
        step_text = (
            ""
            if not queued_steps
            else "\nsteps "
            + "".join(">" if direction > 0 else "<" for direction in queued_steps)
        )
        status_text = (
            f"SPACEPAINT  {status}  {self.playback_rate:g}x\n"
            f"command {current}/{total}: {command_name(self.world, self.commands)}\n"
            f"x {position.x:6.2f}   y {position.y:6.2f}   z {position.z:6.2f}\n"
            f"beam {'ON' if self.world.beam_enabled else 'OFF'}  {style.color_name}  {fade}  "
            f"fill {'ON' if self.world.fill_enabled else 'OFF'}"
            f"{step_text}"
        )
        if self.status_text.text != status_text:
            self.status_text.text = status_text

    def update(self) -> None:
        self.u.camera.ui_lens.set_film_size(
            self.u.camera.ui_size * 0.5 * self.u.window.aspect_ratio,
            self.u.camera.ui_size * 0.5,
        )
        delta_seconds = float(self.u.time.dt)
        self._start_next_step()
        if self._step_direction == 1:
            self._advance_forward_step(delta_seconds)
        elif self._step_direction == -1:
            self._advance_backward_step(delta_seconds)
        else:
            self._advance_playback(delta_seconds)
        self._project_world()
        pose = self.world.pose
        position = pose.position
        self.camera.update(
            (position.x, position.y, position.z),
            pose.orientation,
            artwork_bounds(self.world),
            float(self.u.window.aspect_ratio),
        )
        self._update_axis_labels()

    def _advance_playback(self, delta_seconds: float) -> None:
        """Advance ordinary playback at the viewer-selected rate."""
        self.world = advance(
            self.world,
            self.commands,
            delta_seconds * self.playback_rate,
        )

    def input(self, key: str) -> None:
        self.camera.input(key)
        if key == "space":
            self.step_queue = ()
            self._clear_active_step()
            self.world = set_paused(self.world, not self.world.paused)
        elif key in ("left arrow", "right arrow"):
            if self.world.paused or self._step_direction is not None:
                direction = -1 if key == "left arrow" else 1
                self.step_queue = queue_step(self.step_queue, direction)
            elif key == "right arrow":
                self.playback_rate *= 2.0
            else:
                self.playback_rate = max(1.0, self.playback_rate / 2.0)
        elif key == "r":
            self.step_queue = ()
            self._clear_active_step()
            self.world = initial_world_state()
        elif key == "a":
            self.cycle_axes()
        elif key == "v":
            self.toggle_camera_view()
        elif key == "h":
            self.hud_visible = not self.hud_visible
            self.hud_root.enabled = self.hud_visible
        self._project_world()

    def show_completed_artwork(self) -> None:
        """Project the final program state using the exact default artwork view."""
        self.step_queue = ()
        self._clear_active_step()
        # Freeze at the exact completion instant while Panda3D draws the
        # handful of frames needed to populate the screenshot framebuffer.
        self.world = set_paused(replay_to_completion(self.commands), True)
        self._project_world()
        self.camera.frame_artwork(
            artwork_bounds(self.world),
            float(self.u.window.aspect_ratio),
        )
        self._update_camera_button()
        self._update_axis_labels()


def build_scene(
    config: GameConfig | None = None,
    *,
    student_module: ModuleType | None = None,
) -> SpacepaintScene:
    """Populate an initialized Ursina app and return its scene controller."""
    u = cast(Any, import_module("ursina"))
    resolved = GameConfig() if config is None else config
    if resolved.antialias_samples > 0:
        u.scene.setAntialias(_panda.AntialiasAttrib.MMultisample)
    u.window.color = u.color.rgb32(12, 7, 29)
    showbase_globals = cast(Any, import_module("direct.showbase.ShowBaseGlobal"))
    showbase_globals.base.setBackgroundColor(0.047, 0.027, 0.114, 1.0)
    u.camera.overlay.enabled = False
    if getattr(u.window, "editor_ui", None) is not None:
        u.window.editor_ui.enabled = False
    u.camera.ui_lens.set_film_size(
        u.camera.ui_size * 0.5 * u.window.aspect_ratio,
        u.camera.ui_size * 0.5,
    )
    commands, problem = load_student_program(
        resolved.student_module,
        student_module=student_module,
    )
    return SpacepaintScene(u, resolved, commands, problem)


def create_scene_app(
    config: GameConfig | None = None,
    *,
    window_type: str | None = None,
    student_module: ModuleType | None = None,
) -> tuple[RunnableApp, SpacepaintScene]:
    """Create an app and scene, optionally using an offscreen graphics window."""
    resolved = GameConfig() if config is None else config
    if resolved.antialias_samples > 0:
        _panda.loadPrcFileData(
            "spacepaint-antialiasing",
            f"framebuffer-multisample 1\nmultisamples {resolved.antialias_samples}\n",
        )
    u = cast(Any, import_module("ursina"))
    if window_type is not None:
        application = cast(Any, import_module("ursina.application"))
        asset_folder = Path.cwd().resolve()
        application.asset_folder = asset_folder
        application.scenes_folder = asset_folder / "scenes"
        application.scripts_folder = asset_folder / "scripts"
        application.fonts_folder = asset_folder / "fonts"
        application.compressed_textures_folder = asset_folder / "textures_compressed"
        application.compressed_models_folder = asset_folder / "models_compressed"
        _panda.getModelPath().appendPath(str(asset_folder))
    app_options: dict[str, Any] = {
        "title": resolved.title,
        "borderless": resolved.borderless,
        "fullscreen": resolved.fullscreen,
        "vsync": resolved.vsync,
        "development_mode": resolved.development_mode,
        "size": resolved.size,
    }
    if window_type is not None:
        app_options["window_type"] = window_type
        app_options["editor_ui_enabled"] = False
    app = cast(RunnableApp, u.Ursina(**app_options))
    if window_type is None:
        configure_window(cast(WindowLike, u.window), resolved)
    app.setBackgroundColor(0.045, 0.025, 0.11, 1)
    scene = build_scene(resolved, student_module=student_module)
    return app, scene


def create_app(
    config: GameConfig | None = None,
    *,
    student_module: ModuleType | None = None,
) -> RunnableApp:
    app, _ = create_scene_app(config, student_module=student_module)
    return app


def start_spacepaint(*, student_module: ModuleType | None = None) -> None:
    create_app(student_module=student_module).run()


if __name__ == "__main__":
    start_spacepaint()
