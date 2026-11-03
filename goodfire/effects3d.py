"""PROVIDED: fire, smoke, spark, and ember effects for the 3D viewer.

Nothing here knows about your classes. The viewer tells a FireEffects object
which squares are burning; this file only makes them look alive. Every effect
is a few textured or colored shapes animated each frame:

- flames: three flickering, swaying "tongues" per burning square, drawn with
  additive blending so overlapping fire glows brighter, plus a soft light
  pool on the ground;
- sparks: tiny bright embers that rise and drift downwind;
- smoke: soft round puffs that billow up, grow, lighten, and fade;
- smolder: squares that just burned out glow red for a few seconds.
"""

# Ursina's type hints are incomplete; the provided 3D files relax checking.
# pyright: basic, reportArgumentType=false, reportAttributeAccessIssue=false
# pyright: reportOptionalMemberAccess=false

import math
import random

from panda3d.core import ColorBlendAttrib
from panda3d.core import PNMImage
from panda3d.core import Texture
from ursina import Entity
from ursina import color
from ursina import time
from ursina.mesh import Mesh

Point = tuple[float, float, float]

MAX_SPARKS: int = 160
MAX_SMOKE: int = 110
SMOLDER_SECONDS: float = 4.0


def soft_texture(size: int = 64) -> Texture:
    """Make a white disc whose alpha fades smoothly to 0 at the edge."""
    image: PNMImage = PNMImage(size, size, 4)
    middle: float = (size - 1) / 2
    for x in range(size):
        for y in range(size):
            distance: float = math.hypot(x - middle, y - middle) / middle
            alpha: float = max(0.0, 1.0 - distance) ** 1.6
            image.setXelA(x, y, 1.0, 1.0, 1.0, alpha)
    texture: Texture = Texture("soft")
    texture.load(image)
    return texture


def flame_tongue(core: bool) -> Mesh:
    """A teardrop of fire: bright at the base, red and clear at the tip."""
    profile: list[tuple[float, float]] = [
        (0.0, 0.0),
        (0.26, 0.1),
        (0.3, 0.32),
        (0.22, 0.68),
        (0.11, 1.02),
        (0.0, 1.42),
    ]
    if core:
        shades = [
            (1.0, 0.9, 0.55, 0.75),
            (1.0, 0.82, 0.38, 0.75),
            (1.0, 0.7, 0.24, 0.65),
            (1.0, 0.56, 0.14, 0.5),
            (0.98, 0.42, 0.1, 0.28),
            (0.9, 0.3, 0.08, 0.0),
        ]
        width: float = 0.55
    else:
        shades = [
            (1.0, 0.5, 0.12, 0.7),
            (1.0, 0.42, 0.08, 0.7),
            (0.95, 0.3, 0.05, 0.6),
            (0.85, 0.2, 0.04, 0.42),
            (0.7, 0.12, 0.03, 0.22),
            (0.5, 0.08, 0.02, 0.0),
        ]
        width = 1.0
    sides: int = 9
    vertices: list[Point] = []
    colors: list[color.Color] = []
    for (radius, height), shade in zip(profile, shades, strict=True):
        for side in range(sides):
            angle: float = 2 * math.pi * side / sides
            vertices.append(
                (
                    math.cos(angle) * radius * width,
                    height,
                    math.sin(angle) * radius * width,
                )
            )
            colors.append(color.rgba(*shade))
    triangles: list[tuple[int, int, int]] = []
    for ring in range(len(profile) - 1):
        for side in range(sides):
            a: int = ring * sides + side
            b: int = ring * sides + (side + 1) % sides
            triangles.append((a, b + sides, b))
            triangles.append((a, a + sides, b + sides))
    return Mesh(vertices=vertices, triangles=triangles, colors=colors)


def glowing(entity: Entity) -> Entity:
    """Draw an entity additively: it brightens what is behind it."""
    entity.setAttrib(
        ColorBlendAttrib.make(
            ColorBlendAttrib.MAdd,
            ColorBlendAttrib.OIncomingAlpha,
            ColorBlendAttrib.OOne,
        )
    )
    entity.setDepthWrite(False)
    entity.setLightOff()
    entity.setTwoSided(True)
    entity.setBin("fixed", 20)
    return entity


def soft(entity: Entity) -> Entity:
    """Draw an entity with ordinary transparency, behind the flames."""
    entity.setTransparency(True)
    entity.setDepthWrite(False)
    entity.setLightOff()
    entity.setBin("fixed", 10)
    return entity


class Particle:
    """One spark or smoke puff: an entity plus how it moves and fades."""

    def __init__(
        self, entity: Entity, velocity: Point, life: float, grow: float
    ):
        """Remember the entity and how long it has to live."""
        self.entity = entity
        self.velocity = velocity
        self.life = life
        self.age = 0.0
        self.grow = grow
        self.start_scale = entity.scale_x


class FireEffects:
    """Animate flames, sparks, smoke, and smoldering ground."""

    def __init__(self, seed: int = 11):
        """Build the shared meshes and texture once."""
        self.rng = random.Random(seed)
        self.texture: Texture = soft_texture()
        self.outer: Mesh = flame_tongue(False)
        self.inner: Mesh = flame_tongue(True)
        self.root: Entity = Entity()
        self.flames: dict[tuple[int, int], tuple[Entity, list[Entity]]] = {}
        self.smolder: dict[tuple[int, int], tuple[Entity, float]] = {}
        self.sparks: list[Particle] = []
        self.smoke: list[Particle] = []
        self.wind: tuple[float, float] = (0.0, 0.0)
        self.clock = 0.0

    # ------------------------------------------------------------ flames

    def set_burning(
        self, key: tuple[int, int], where: Point, burning: bool
    ) -> None:
        """Start or stop the flames on one square."""
        if burning and key not in self.flames:
            self._light(key, where)
        elif not burning and key in self.flames:
            cluster, _tongues = self.flames.pop(key)
            cluster.disable()
            self._start_smolder(key, where)

    def _light(self, key: tuple[int, int], where: Point) -> None:
        x, y, z = where
        cluster: Entity = Entity(parent=self.root, position=(x, y, z))
        pool: Entity = glowing(
            Entity(
                parent=cluster,
                model="quad",
                color=color.rgba(1.0, 0.45, 0.12, 0.6),
                scale=2.2,
                rotation_x=90,
                y=0.05,
            )
        )
        pool.setTexture(self.texture, 1)
        tongues: list[Entity] = []
        for index in range(3):
            angle: float = index * 2.1 + self.rng.uniform(-0.4, 0.4)
            reach: float = self.rng.uniform(0.08, 0.3)
            size: float = self.rng.uniform(1.5, 2.3)
            for mesh, scale in ((self.outer, 1.0), (self.inner, 0.62)):
                tongue: Entity = Entity(
                    parent=cluster,
                    position=(
                        math.cos(angle) * reach,
                        0.0,
                        math.sin(angle) * reach,
                    ),
                    scale=size * scale,
                )
                # Many squares share one mesh, so each gets an instance.
                mesh.instanceTo(tongue)
                glowing(tongue)
                tongue.phase = self.rng.uniform(0, 2 * math.pi)
                tongue.base_scale = size * scale
                tongues.append(tongue)
        self.flames[key] = (cluster, tongues)

    def _start_smolder(self, key: tuple[int, int], where: Point) -> None:
        x, y, z = where
        ember: Entity = glowing(
            Entity(
                parent=self.root,
                model="quad",
                color=color.rgba(0.9, 0.2, 0.05, 0.7),
                position=(x, y + 0.04, z),
                rotation_x=90,
                scale=1.4,
            )
        )
        ember.setTexture(self.texture, 1)
        if key in self.smolder:
            self.smolder[key][0].disable()
        self.smolder[key] = (ember, self.clock + SMOLDER_SECONDS)

    def clear(self) -> None:
        """Remove every effect (used when the season restarts)."""
        for cluster, _tongues in self.flames.values():
            cluster.disable()
        for ember, _until in self.smolder.values():
            ember.disable()
        for particle in self.sparks + self.smoke:
            particle.entity.disable()
        self.flames.clear()
        self.smolder.clear()
        self.sparks.clear()
        self.smoke.clear()

    # ------------------------------------------------------------ particles

    def _spawn_spark(self, where: Point) -> None:
        x, y, z = where
        spark: Entity = glowing(
            Entity(
                parent=self.root,
                model="quad",
                billboard=True,
                color=color.rgba(1.0, self.rng.uniform(0.55, 0.85), 0.25, 1),
                position=(
                    x + self.rng.uniform(-0.4, 0.4),
                    y + 0.6,
                    z + self.rng.uniform(-0.4, 0.4),
                ),
                scale=self.rng.uniform(0.2, 0.32),
            )
        )
        spark.setTexture(self.texture, 1)
        wind_x, wind_z = self.wind
        self.sparks.append(
            Particle(
                spark,
                (
                    wind_x * 0.5 + self.rng.uniform(-0.4, 0.4),
                    self.rng.uniform(1.6, 3.2),
                    wind_z * 0.5 + self.rng.uniform(-0.4, 0.4),
                ),
                self.rng.uniform(0.9, 1.8),
                -0.5,
            )
        )

    def _spawn_smoke(self, where: Point) -> None:
        x, y, z = where
        gray: float = self.rng.uniform(0.28, 0.4)
        puff: Entity = soft(
            Entity(
                parent=self.root,
                model="quad",
                billboard=True,
                color=color.rgba(gray, gray * 0.96, gray * 0.92, 0.0),
                position=(
                    x + self.rng.uniform(-0.3, 0.3),
                    y + 2.6,
                    z + self.rng.uniform(-0.3, 0.3),
                ),
                scale=self.rng.uniform(1.8, 2.6),
                rotation_z=self.rng.uniform(0, 360),
            )
        )
        puff.setTexture(self.texture, 1)
        wind_x, wind_z = self.wind
        self.smoke.append(
            Particle(
                puff,
                (wind_x * 0.35, self.rng.uniform(1.1, 1.6), wind_z * 0.35),
                self.rng.uniform(3.0, 4.5),
                0.35,
            )
        )

    # ------------------------------------------------------------ each frame

    def update(self, centers: dict[tuple[int, int], Point]) -> None:
        """Animate everything; `centers` maps burning squares to positions."""
        dt: float = time.dt
        self.clock += dt
        for cluster, tongues in self.flames.values():
            for tongue in tongues:
                t: float = self.clock * 9 + tongue.phase
                flicker: float = (
                    1 + 0.18 * math.sin(t) + 0.1 * math.sin(t * 2.7 + 1.3)
                )
                tongue.scale_y = tongue.base_scale * flicker * 1.25
                tongue.scale_x = tongue.base_scale * (2 - flicker) * 0.95
                tongue.rotation_z = 7 * math.sin(t * 0.6)
                tongue.rotation_x = 7 * math.cos(t * 0.5)
            cluster.children[0].alpha = 0.5 + 0.12 * math.sin(self.clock * 6)

        burning: list[Point] = list(centers.values())
        if burning:
            for _ in range(min(3, len(burning))):
                if len(self.sparks) < MAX_SPARKS and self.rng.random() < 0.8:
                    self._spawn_spark(self.rng.choice(burning))
            for _ in range(min(3, 1 + len(burning) // 12)):
                if len(self.smoke) < MAX_SMOKE and self.rng.random() < 0.6:
                    self._spawn_smoke(self.rng.choice(burning))

        for particle in list(self.sparks):
            self._move(particle, dt)
            fade: float = 1 - particle.age / particle.life
            particle.entity.alpha = max(fade, 0.0)
            if particle.age >= particle.life:
                self.sparks.remove(particle)
                particle.entity.disable()

        for particle in list(self.smoke):
            self._move(particle, dt)
            share: float = particle.age / particle.life
            # Fade in quickly, then thin out as the puff rises and spreads.
            alpha: float = min(share * 6, 1.0) * (1 - share) * 0.8
            light: float = 0.32 + 0.35 * share
            particle.entity.color = color.rgba(
                light, light * 0.97, light * 0.94, alpha
            )
            if share >= 1:
                self.smoke.remove(particle)
                particle.entity.disable()

        for key, (ember, until) in list(self.smolder.items()):
            left: float = (until - self.clock) / SMOLDER_SECONDS
            ember.alpha = max(left, 0.0) * (
                0.55 + 0.15 * math.sin(self.clock * 3 + key[0])
            )
            if left <= 0:
                ember.disable()
                del self.smolder[key]

    def _move(self, particle: Particle, dt: float) -> None:
        particle.age += dt
        vx, vy, vz = particle.velocity
        entity: Entity = particle.entity
        entity.x += vx * dt
        entity.y += vy * dt
        entity.z += vz * dt
        entity.scale = max(
            particle.start_scale * (1 + particle.grow * particle.age), 0.02
        )
