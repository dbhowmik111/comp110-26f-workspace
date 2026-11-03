"""PROVIDED: a 3D sand-table view of any simulation, built with Ursina.

This viewer never imports your classes. It only uses:

- the Simulation protocol: ``cell_at``, ``ignite``, ``step``, and ``str()``
- the Land protocol: ``row``, ``col``, ``color()``, and ``str(cell)``
- the Burnable protocol: ``fuel``, ``can_ignite()``, and ``is_burning()``
- the Rendered protocol, if a square has it: ``appearance()``
- the HasWeather protocol, if the simulation has it: ``weather_report()``
  and ``water_drops()``

So Part 1's Landscape and Part 2's Wildfire both appear here, and any new
kind of square you invent shows up without changes to this file.
"""

# Ursina's type hints are incomplete: it accepts plain tuples where its hints
# say Vec3, and it sets time.dt while running. Only the provided 3D files
# relax checking; your own files keep strict checking.
# pyright: basic, reportArgumentType=false, reportAttributeAccessIssue=false

import math
import random
from collections.abc import Callable

# Load Qt (through comp110_gui) before the 3D engine. On Windows the 3D
# engine's bundled C++ runtime DLL would otherwise load first, and Qt then
# crashes while starting up (exit code 0xC0000005).
import comp110_gui  # noqa: F401  (must stay above the ursina imports)
from ursina import Entity
from ursina import Sky
from ursina import Text
from ursina import camera
from ursina import color
from ursina import mouse
from ursina import scene
from ursina import time
from ursina import window
from ursina.mesh import Mesh
from ursina.prefabs.editor_camera import EditorCamera

import effects3d
import models3d
from goodfire import terrain
from goodfire.part2_protocols import HasWeather
from goodfire.part2_protocols import Rendered
from goodfire.part2_protocols import Simulation
from goodfire.protocols import Burnable
from goodfire.protocols import Land

Y_SCALE: float = 0.09
"""Vertical exaggeration: one meter of elevation is this many world units."""

HALF: float = terrain.GRID_SIZE / 2


def corner_height(row: int, col: int) -> float:
    """Return the world height of a grid corner (the average of its squares)."""
    total: float = 0.0
    count: int = 0
    for r in (row - 1, row):
        for c in (col - 1, col):
            if 0 <= r < terrain.GRID_SIZE and 0 <= c < terrain.GRID_SIZE:
                total += terrain.elevation(r, c)
                count += 1
    return total / count * Y_SCALE


def world_x(col: float) -> float:
    """Convert a column (or column edge) to a world x coordinate."""
    return col - HALF


def world_z(row: float) -> float:
    """Convert a row to a world z coordinate. North (row 0) is far away."""
    return HALF - row


def square_center(row: int, col: int) -> tuple[float, float, float]:
    """Return the world position at the middle of one square's surface."""
    height: float = (
        corner_height(row, col)
        + corner_height(row, col + 1)
        + corner_height(row + 1, col)
        + corner_height(row + 1, col + 1)
    ) / 4
    return (world_x(col + 0.5), height, world_z(row + 0.5))


def hex_to_rgb(text: str) -> tuple[int, int, int]:
    """Turn a "#RRGGBB" string from a cell's color() into channels."""
    return (int(text[1:3], 16), int(text[3:5], 16), int(text[5:7], 16))


def plant_state(cell: Burnable) -> str:
    """Describe a burnable square as "growing", "burning", or "burned"."""
    if cell.is_burning():
        return "burning"
    if cell.can_ignite():
        return "growing"
    return "burned"


def model_key(cell: Land) -> str | None:
    """Choose which shared 3D model a square shows right now, or None."""
    if not isinstance(cell, Rendered):
        return None
    kind: str = cell.appearance()
    if not isinstance(cell, Burnable):
        return None  # water, roads, and cleared soil are part of the ground
    state: str = plant_state(cell)
    if kind == "home":
        if state == "burned":
            return "damaged_house"
        return "firewise_house" if getattr(cell, "hardened", False) else "house"
    if kind == "pine":
        return "scorched_pine" if state == "burned" else "pine"
    if kind == "hardwood":
        return "stump" if state == "burned" else "hardwood"
    if kind == "grass":
        return None if state == "burned" else "grass"
    return None


def model_scale(cell: Land, key: str) -> float:
    """Scale plants by fuel: thinned or treated stands look lighter."""
    if key in ("house", "firewise_house", "damaged_house", "stump"):
        return 1.0
    fuel: float = cell.fuel if isinstance(cell, Burnable) else 1.0
    return 0.75 + 0.35 * fuel


class ForestViewer3D:
    """Draw a simulation as a 3D sand table and run its fire over time."""

    def __init__(
        self, make_sim: Callable[[], Simulation], steps_per_second: float
    ):
        """Build the scene for a new simulation.

        Args:
            make_sim: Creates a fresh simulation; called again on restart.
            steps_per_second: How fast the fire advances while running.
        """
        self.make_sim = make_sim
        self.sim: Simulation = make_sim()
        self.steps_per_second = steps_per_second
        self.paused = False
        self.clock = 0.0
        self.age = 0.0
        self.haze = 0.0
        self.rng = random.Random(7)
        self.models: dict[str, Mesh] = {
            "pine": models3d.pine(False),
            "scorched_pine": models3d.pine(True),
            "hardwood": models3d.hardwood(),
            "grass": models3d.grass(),
            "house": models3d.house(False),
            "firewise_house": models3d.house(True),
            "damaged_house": models3d.damaged_house(),
            "stump": models3d.stump(),
        }
        self.effects = effects3d.FireEffects()
        self.burning: dict[tuple[int, int], tuple[float, float, float]] = {}

        window.color = color.rgb32(196, 214, 230)
        self.sky = Sky(texture="sky_default")
        scene.fog_color = color.rgb32(206, 220, 232)
        scene.fog_density = (40, 110)
        self.terrain = self._build_terrain()
        self.base = Entity(
            model="cube",
            color=color.rgb32(92, 74, 56),
            position=(0, -1.5, 0),
            scale=(terrain.GRID_SIZE, 3, terrain.GRID_SIZE),
        )
        self.water: Entity | None = None
        self.holders: dict[tuple[int, int], Entity] = {}
        self.shown: dict[tuple[int, int], str | None] = {}
        self.drops: list[tuple[Entity, float]] = []
        self.helicopter = Entity(
            model=models3d.helicopter(), enabled=False, double_sided=True
        )
        self._place_models()

        self._build_hud()
        self.camera_rig = EditorCamera(rotation=(38, 0, 0))
        # The orbit camera zooms toward target_z, so set both to start far
        # enough back to see the whole map.
        camera.position = (0, 0, -46)
        self.camera_rig.target_z = -46
        self.refresh()

    # ------------------------------------------------------------ building

    def _build_hud(self) -> None:
        """Make the on-screen panels: status, legend, inspector, controls."""
        ink: color.Color = color.rgba(0.97, 0.96, 0.93, 1)
        self.status_panel = Entity(
            parent=camera.ui,
            model="quad",
            color=color.rgba(0.07, 0.09, 0.11, 0.62),
            origin=(-0.5, 0.5),
            position=window.top_left + (0.015, -0.015),
        )
        self.status = Text(
            "",
            parent=camera.ui,
            origin=(-0.5, 0.5),
            position=window.top_left + (0.03, -0.028),
            scale=0.95,
            color=ink,
            line_height=1.25,
        )
        self.hover_panel = Entity(
            parent=camera.ui,
            model="quad",
            color=color.rgba(0.07, 0.09, 0.11, 0.62),
            origin=(-0.5, -0.5),
            position=window.bottom_left + (0.015, 0.06),
            enabled=False,
        )
        self.hover = Text(
            "",
            parent=camera.ui,
            origin=(-0.5, -0.5),
            position=window.bottom_left + (0.03, 0.072),
            scale=0.9,
            color=ink,
        )
        Entity(
            parent=camera.ui,
            model="quad",
            color=color.rgba(0.07, 0.09, 0.11, 0.55),
            origin=(0, -0.5),
            position=(0, window.bottom.y),
            scale=(window.aspect_ratio, 0.045),
        )
        Text(
            "Click: light a fire    Space: pause    S: one step    "
            "R: restart    Up/Down: speed    Right-drag: orbit    "
            "Scroll: zoom",
            parent=camera.ui,
            origin=(0, -0.5),
            position=(0, window.bottom.y + 0.013),
            scale=0.78,
            color=color.rgba(0.85, 0.86, 0.84, 1),
        )
        legend: list[tuple[str, tuple[int, int, int]]] = [
            ("Longleaf pine", models3d.PINE_NEEDLES),
            ("Scorched (survived)", models3d.SCORCHED_NEEDLES),
            ("Hardwood", models3d.LEAVES),
            ("Grass meadow", (176, 168, 86)),
            ("Home", (162, 84, 58)),
            ("Firewise home (metal roof)", (96, 112, 128)),
            ("Fuel break", (138, 106, 72)),
            ("Burned ground", (46, 42, 38)),
            ("Water", (56, 128, 199)),
        ]
        top: float = window.top_right.y - 0.015
        right: float = window.top_right.x - 0.015
        height: float = 0.04 + 0.034 * len(legend)
        Entity(
            parent=camera.ui,
            model="quad",
            color=color.rgba(0.07, 0.09, 0.11, 0.62),
            origin=(0.5, 0.5),
            position=(right, top),
            scale=(0.33, height),
        )
        for index, (label, rgb) in enumerate(legend):
            y: float = top - 0.03 - 0.034 * index
            Entity(
                parent=camera.ui,
                model="quad",
                color=color.rgb32(*rgb),
                position=(right - 0.305, y),
                scale=0.022,
            )
            Text(
                label,
                parent=camera.ui,
                origin=(-0.5, 0),
                position=(right - 0.285, y),
                scale=0.78,
                color=ink,
            )

    def _build_terrain(self) -> Entity:
        """Make one mesh with a separately colored quad for every square."""
        vertices: list[tuple[float, float, float]] = []
        triangles: list[tuple[int, int, int]] = []
        for row in range(terrain.GRID_SIZE):
            for col in range(terrain.GRID_SIZE):
                first: int = len(vertices)
                for d_row, d_col in ((0, 0), (0, 1), (1, 1), (1, 0)):
                    vertices.append(
                        (
                            world_x(col + d_col),
                            corner_height(row + d_row, col + d_col),
                            world_z(row + d_row),
                        )
                    )
                triangles.append((first, first + 1, first + 2))
                triangles.append((first, first + 2, first + 3))
        self.terrain_mesh = Mesh(
            vertices=vertices,
            triangles=triangles,
            colors=[color.white] * len(vertices),
        )
        self.normals: list[tuple[float, float, float]] = []
        for row in range(terrain.GRID_SIZE):
            for col in range(terrain.GRID_SIZE):
                west = (
                    corner_height(row, col) + corner_height(row + 1, col)
                ) / 2
                east = (
                    corner_height(row, col + 1)
                    + corner_height(row + 1, col + 1)
                ) / 2
                north = (
                    corner_height(row, col) + corner_height(row, col + 1)
                ) / 2
                south = (
                    corner_height(row + 1, col)
                    + corner_height(row + 1, col + 1)
                ) / 2
                self.normals.append((west - east, 1.0, south - north))
        self.texture_noise: list[float] = [
            1.0 + self.rng.uniform(-0.05, 0.05)
            for _ in range(terrain.GRID_SIZE**2)
        ]
        ground: Entity = Entity(
            model=self.terrain_mesh, collider="mesh", double_sided=True
        )
        ground.on_click = self._ignite_under_mouse
        return ground

    def _build_water(self) -> None:
        """Lay a translucent water surface over every water square."""
        if self.water is not None:
            self.water.disable()
            self.water = None
        vertices: list[tuple[float, float, float]] = []
        triangles: list[tuple[int, int, int]] = []
        for row in range(terrain.GRID_SIZE):
            for col in range(terrain.GRID_SIZE):
                cell: Land = self.sim.cell_at(row, col)
                if (
                    not isinstance(cell, Rendered)
                    or cell.appearance() != "water"
                ):
                    continue
                _x, y, _z = square_center(row, col)
                first: int = len(vertices)
                for d_row, d_col in ((0, 0), (0, 1), (1, 1), (1, 0)):
                    vertices.append(
                        (world_x(col + d_col), y + 0.06, world_z(row + d_row))
                    )
                triangles.append((first, first + 1, first + 2))
                triangles.append((first, first + 2, first + 3))
        if vertices:
            self.water = Entity(
                model=Mesh(vertices=vertices, triangles=triangles),
                color=color.rgba(0.22, 0.5, 0.78, 0.78),
                double_sided=True,
            )

    def _place_models(self) -> None:
        """Create one empty holder per square; models are attached later."""
        for holder in self.holders.values():
            holder.disable()
        self.holders.clear()
        self.shown.clear()
        for row in range(terrain.GRID_SIZE):
            for col in range(terrain.GRID_SIZE):
                x, y, z = square_center(row, col)
                holder: Entity = Entity(
                    position=(
                        x + self.rng.uniform(-0.12, 0.12),
                        y,
                        z + self.rng.uniform(-0.12, 0.12),
                    ),
                    rotation_y=self.rng.uniform(0, 360),
                )
                holder.setTwoSided(True)
                self.holders[(row, col)] = holder
                self.shown[(row, col)] = None
        self._build_water()

    # ------------------------------------------------------------ updating

    def refresh(self) -> None:
        """Make the scene match the simulation's current state."""
        colors: list[color.Color] = []
        index: int = 0
        for row in range(terrain.GRID_SIZE):
            for col in range(terrain.GRID_SIZE):
                cell: Land = self.sim.cell_at(row, col)
                rgb = hex_to_rgb(cell.color())
                noise: float = self.texture_noise[index]
                shaded: color.Color = models3d.shade(
                    (
                        min(round(rgb[0] * noise), 255),
                        min(round(rgb[1] * noise), 255),
                        min(round(rgb[2] * noise), 255),
                    ),
                    models3d._normalize(self.normals[index]),
                )
                colors.extend([shaded] * 4)
                self._update_model(row, col, cell)
                burning: bool = isinstance(cell, Burnable) and cell.is_burning()
                self._update_flame(row, col, burning)
                index += 1
        self.terrain_mesh.colors = colors
        self.terrain_mesh.generate()

        wind = getattr(self.sim, "wind", None)
        current = wind() if callable(wind) else None
        if current is not None:
            heading: float = math.radians(getattr(current, "toward", 0.0))
            speed: float = getattr(current, "speed", 0.0)
            self.effects.wind = (
                math.sin(heading) * speed / 4,
                math.cos(heading) * speed / 4,
            )

        text: str = f"Good Fire\n{self.sim}"
        if self.paused:
            text += "  ·  paused"
        if isinstance(self.sim, HasWeather):
            text += f"\n{self.sim.weather_report()}"
            for drop in self.sim.water_drops():
                self._start_drop(drop)
        self.status.text = text
        self.status_panel.scale = (
            self.status.width * 0.93 + 0.03,
            self.status.height + 0.03,
        )

    def _update_model(self, row: int, col: int, cell: Land) -> None:
        """Swap a square's 3D model when its kind or state changes."""
        key: str | None = model_key(cell)
        holder: Entity = self.holders[(row, col)]
        if key != self.shown[(row, col)]:
            holder.node().removeAllChildren()
            if key is not None:
                self.models[key].instanceTo(holder)
            self.shown[(row, col)] = key
        if key is not None:
            size: float = model_scale(cell, key)
            holder.scale = (size, size, size)
            burning: bool = isinstance(cell, Burnable) and cell.is_burning()
            if burning:
                holder.setColorScale(0.55, 0.36, 0.28, 1)
            else:
                holder.setColorScale(1, 1, 1, 1)

    def _update_flame(self, row: int, col: int, burning: bool) -> None:
        """Tell the effects which squares are burning."""
        key: tuple[int, int] = (row, col)
        if burning:
            self.burning[key] = square_center(row, col)
        else:
            self.burning.pop(key, None)
        self.effects.set_burning(key, square_center(row, col), burning)

    def _start_drop(self, drop: tuple[float, float, float]) -> None:
        """Fly the helicopter over a drop and let the water fall."""
        row, col, radius = drop
        x, z = world_x(col), world_z(row)
        y: float = square_center(int(row), int(col))[1]
        self.helicopter.enabled = True
        self.helicopter.position = (x - 6, y + 7, z - 6)
        self.helicopter.animate_position((x, y + 5, z), duration=0.6)
        for _ in range(int(40 * radius)):
            angle: float = self.rng.uniform(0, 2 * math.pi)
            reach: float = radius * math.sqrt(self.rng.random())
            water: Entity = Entity(
                model="sphere",
                color=color.rgba(0.55, 0.78, 0.95, 0.8),
                scale=0.16,
                position=(x, y + 3.2, z),
            )
            water.animate_position(
                (
                    x + math.cos(angle) * reach,
                    y + 0.1,
                    z + math.sin(angle) * reach,
                ),
                duration=self.rng.uniform(0.6, 1.0),
                delay=0.5,
            )
            self.drops.append((water, self.age + 1.8))

    def _ignite_under_mouse(self) -> None:
        """Start a fire on the square under the mouse pointer."""
        point = mouse.world_point
        if point is None:
            return
        row, col = self._square_at(point.x, point.z)
        if self.sim.ignite(row, col):
            self.refresh()

    def _square_at(self, x: float, z: float) -> tuple[int, int]:
        """Return the (row, col) of the square under a world position."""
        last: int = terrain.GRID_SIZE - 1
        col: int = min(max(int(x + HALF), 0), last)
        row: int = min(max(int(HALF - z), 0), last)
        return (row, col)

    def advance(self, steps: int) -> None:
        """Run the fire forward, then redraw once."""
        for _ in range(steps):
            self.sim.step()
        self.refresh()

    def restart(self) -> None:
        """Replace the simulation with a fresh one and redraw everything."""
        self.sim = self.make_sim()
        self.effects.clear()
        self.burning.clear()
        self._place_models()
        self.refresh()

    # ------------------------------------------------------------ Ursina hooks

    def update(self) -> None:
        """Called by Ursina every frame: animate, then step the fire."""
        self.age += time.dt
        self.effects.update(self.burning)
        self._update_haze()
        self._update_drops()
        self._update_hover()
        if self.paused:
            return
        self.clock += time.dt
        if self.clock >= 1 / self.steps_per_second:
            self.clock = 0.0
            self.advance(1)

    def _update_haze(self) -> None:
        """Warm the sky toward smoky amber as more squares burn."""
        target: float = min(len(self.burning) / 60, 1.0)
        self.haze += (target - self.haze) * min(time.dt * 1.5, 1.0)
        tint: float = 1 - 0.25 * self.haze
        self.sky.color = color.rgba(
            1.0, 0.9 + 0.1 * tint, 0.75 + 0.25 * tint, 1.0
        )

    def _update_drops(self) -> None:
        """Clear water droplets once they land; send the helicopter home."""
        for water, expires in list(self.drops):
            if self.age >= expires:
                self.drops.remove((water, expires))
                water.disable()
        if not self.drops and self.helicopter.enabled:
            self.helicopter.x += 6 * time.dt
            self.helicopter.y += 2 * time.dt
            if self.helicopter.y > 20:
                self.helicopter.enabled = False

    def _update_hover(self) -> None:
        """Show str() of the square under the mouse, like Part 1's inspector."""
        text: str = ""
        if mouse.hovered_entity is self.terrain and mouse.world_point:
            row, col = self._square_at(mouse.world_point.x, mouse.world_point.z)
            text = str(self.sim.cell_at(row, col))
        if text != self.hover.text:
            self.hover.text = text
            self.hover_panel.enabled = bool(text)
            if text:
                self.hover_panel.scale = (
                    self.hover.width * 0.93 + 0.03,
                    self.hover.height + 0.025,
                )

    def input(self, key: str) -> None:
        """Called by Ursina for key presses."""
        if key == "space":
            self.paused = not self.paused
            self.refresh()
        elif key == "s":
            self.advance(1)
        elif key == "r":
            self.restart()
        elif key == "up arrow":
            self.steps_per_second = min(self.steps_per_second * 1.5, 30)
        elif key == "down arrow":
            self.steps_per_second = max(self.steps_per_second / 1.5, 0.5)
