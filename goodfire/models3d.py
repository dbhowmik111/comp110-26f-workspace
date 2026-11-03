"""PROVIDED: low-poly 3D models with lighting baked into their colors.

Each model is built once from simple shapes (boxes, cylinders, cones, and
faceted blobs). Every triangle gets its own color, brightened or darkened by
how directly it faces the sun, so the models look lit on any computer
without special shaders. The viewer shares one copy of each model among all
the squares that use it.
"""

# Ursina's type hints are incomplete; only the provided 3D files relax
# checking. Your own files keep strict checking.
# pyright: basic, reportArgumentType=false, reportAttributeAccessIssue=false

import math

from ursina import color
from ursina.mesh import Mesh

Vec = tuple[float, float, float]
RGB = tuple[int, int, int]

SUN: Vec = (-0.42, 0.82, -0.38)
"""Direction toward the sun: up, a little west, and toward the camera."""

AMBIENT: float = 0.52
DIFFUSE: float = 0.62


def _normalize(v: Vec) -> Vec:
    length: float = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0
    return (v[0] / length, v[1] / length, v[2] / length)


SUN_DIRECTION: Vec = _normalize(SUN)


def shade(rgb: RGB, normal: Vec) -> color.Color:
    """Return a color brightened by how directly a face points at the sun."""
    facing: float = max(
        0.0,
        normal[0] * SUN_DIRECTION[0]
        + normal[1] * SUN_DIRECTION[1]
        + normal[2] * SUN_DIRECTION[2],
    )
    light: float = AMBIENT + DIFFUSE * facing
    return color.rgba(
        min(rgb[0] * light / 255, 1.0),
        min(rgb[1] * light / 255, 1.0),
        min(rgb[2] * light / 255, 1.0),
        1.0,
    )


class LowPoly:
    """Collects flat-shaded triangles, then becomes one Mesh."""

    def __init__(self):
        self.vertices: list[Vec] = []
        self.triangles: list[tuple[int, int, int]] = []
        self.colors: list[color.Color] = []

    def triangle(
        self, a: Vec, b: Vec, c: Vec, rgb: RGB, center: Vec | None = None
    ) -> None:
        """Add one triangle; if ``center`` is given, face away from it."""
        u: Vec = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        v: Vec = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        normal: Vec = _normalize(
            (
                u[1] * v[2] - u[2] * v[1],
                u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0],
            )
        )
        if center is not None:
            middle: Vec = (
                (a[0] + b[0] + c[0]) / 3 - center[0],
                (a[1] + b[1] + c[1]) / 3 - center[1],
                (a[2] + b[2] + c[2]) / 3 - center[2],
            )
            outward: float = (
                normal[0] * middle[0]
                + normal[1] * middle[1]
                + normal[2] * middle[2]
            )
            if outward < 0:
                normal = (-normal[0], -normal[1], -normal[2])
                b, c = c, b
        shaded: color.Color = shade(rgb, normal)
        first: int = len(self.vertices)
        self.vertices += [a, b, c]
        self.colors += [shaded, shaded, shaded]
        self.triangles.append((first, first + 1, first + 2))

    def quad(
        self,
        a: Vec,
        b: Vec,
        c: Vec,
        d: Vec,
        rgb: RGB,
        center: Vec | None = None,
    ) -> None:
        """Add a four-sided face as two triangles."""
        self.triangle(a, b, c, rgb, center)
        self.triangle(a, c, d, rgb, center)

    def box(self, center: Vec, size: Vec, rgb: RGB) -> None:
        """Add an axis-aligned box."""
        x, y, z = center
        w, h, d = size[0] / 2, size[1] / 2, size[2] / 2
        p = [
            (x - w, y - h, z - d),
            (x + w, y - h, z - d),
            (x + w, y + h, z - d),
            (x - w, y + h, z - d),
            (x - w, y - h, z + d),
            (x + w, y - h, z + d),
            (x + w, y + h, z + d),
            (x - w, y + h, z + d),
        ]
        self.quad(p[0], p[3], p[2], p[1], rgb, center)  # front (-z)
        self.quad(p[5], p[6], p[7], p[4], rgb, center)  # back (+z)
        self.quad(p[4], p[7], p[3], p[0], rgb, center)  # left
        self.quad(p[1], p[2], p[6], p[5], rgb, center)  # right
        self.quad(p[3], p[7], p[6], p[2], rgb, center)  # top
        self.quad(p[4], p[0], p[1], p[5], rgb, center)  # bottom

    def cylinder(
        self, base: Vec, radius: float, height: float, rgb: RGB, sides: int = 6
    ) -> None:
        """Add an upright cylinder (a trunk or a chimney)."""
        x, y, z = base
        ring: list[tuple[float, float]] = [
            (
                math.cos(2 * math.pi * i / sides),
                math.sin(2 * math.pi * i / sides),
            )
            for i in range(sides)
        ]
        for i in range(sides):
            c0, s0 = ring[i]
            c1, s1 = ring[(i + 1) % sides]
            self.quad(
                (x + radius * c0, y, z + radius * s0),
                (x + radius * c0, y + height, z + radius * s0),
                (x + radius * c1, y + height, z + radius * s1),
                (x + radius * c1, y, z + radius * s1),
                rgb,
                (x, y + height / 2, z),
            )

    def cone(
        self, base: Vec, radius: float, height: float, rgb: RGB, sides: int = 7
    ) -> None:
        """Add an upright cone (a grass tuft or a flame)."""
        x, y, z = base
        tip: Vec = (x, y + height, z)
        for i in range(sides):
            a0: float = 2 * math.pi * i / sides
            a1: float = 2 * math.pi * (i + 1) / sides
            self.triangle(
                (x + radius * math.cos(a0), y, z + radius * math.sin(a0)),
                tip,
                (x + radius * math.cos(a1), y, z + radius * math.sin(a1)),
                rgb,
                (x, y + height / 3, z),
            )

    def blob(self, center: Vec, radii: Vec, rgb: RGB) -> None:
        """Add a faceted ellipsoid (a crown of leaves or a puff of smoke)."""
        x, y, z = center
        rx, ry, rz = radii
        bands: int = 4
        sides: int = 7
        points: list[list[Vec]] = []
        for band in range(bands + 1):
            phi: float = math.pi * band / bands
            row: list[Vec] = []
            for side in range(sides):
                theta: float = 2 * math.pi * side / sides + band * 0.35
                row.append(
                    (
                        x + rx * math.sin(phi) * math.cos(theta),
                        y + ry * math.cos(phi),
                        z + rz * math.sin(phi) * math.sin(theta),
                    )
                )
            points.append(row)
        for band in range(bands):
            for side in range(sides):
                nxt: int = (side + 1) % sides
                a, b = points[band][side], points[band][nxt]
                c, d = points[band + 1][nxt], points[band + 1][side]
                if band == 0:
                    self.triangle(a, c, d, rgb, center)
                elif band == bands - 1:
                    self.triangle(a, b, d, rgb, center)
                else:
                    self.quad(a, b, c, d, rgb, center)

    def gable_roof(
        self, center: Vec, width: float, depth: float, height: float, rgb: RGB
    ) -> None:
        """Add a triangular-prism roof whose ridge runs front to back."""
        x, y, z = center
        w, d = width / 2, depth / 2
        left_front: Vec = (x - w, y, z - d)
        right_front: Vec = (x + w, y, z - d)
        top_front: Vec = (x, y + height, z - d)
        left_back: Vec = (x - w, y, z + d)
        right_back: Vec = (x + w, y, z + d)
        top_back: Vec = (x, y + height, z + d)
        gable: RGB = (228, 214, 190)
        middle: Vec = (x, y + height / 3, z)
        self.triangle(left_front, top_front, right_front, gable, middle)
        self.triangle(right_back, top_back, left_back, gable, middle)
        self.quad(left_back, top_back, top_front, left_front, rgb, middle)
        self.quad(right_front, top_front, top_back, right_back, rgb, middle)

    def mesh(self) -> Mesh:
        """Return the collected triangles as one Ursina mesh."""
        return Mesh(
            vertices=self.vertices,
            triangles=self.triangles,
            colors=self.colors,
        )


# ------------------------------------------------------------------ models

BARK: RGB = (126, 86, 54)
PINE_NEEDLES: RGB = (44, 94, 46)
SCORCHED_NEEDLES: RGB = (150, 88, 44)
SURVIVING_NEEDLES: RGB = (92, 104, 48)
LEAVES: RGB = (86, 140, 64)
CHAR: RGB = (40, 34, 30)


def pine(scorched: bool) -> Mesh:
    """A longleaf pine: a tall straight trunk with tufted crowns at the top.

    After a surface fire the longleaf usually survives with a scorched crown.
    """
    model: LowPoly = LowPoly()
    model.cylinder((0, 0, 0), 0.055, 2.15, BARK, sides=5)
    if scorched:
        # Blackened bark low on the trunk, where the surface fire passed.
        model.cylinder((0, 0, 0), 0.062, 0.55, CHAR, sides=5)
    for index, (x, y, z, r) in enumerate(
        [
            (0.0, 2.2, 0.0, 0.34),
            (0.2, 1.96, 0.06, 0.24),
            (-0.18, 2.0, -0.08, 0.26),
            (0.04, 1.74, -0.16, 0.2),
        ]
    ):
        # Crown scorch browns the lower needles; the protected top tuft
        # (where longleaf keeps its buds) stays green.
        needles: RGB = PINE_NEEDLES
        if scorched:
            needles = SURVIVING_NEEDLES if index == 0 else SCORCHED_NEEDLES
            if index == 0:
                r = 0.2
        model.blob((x, y, z), (r * 1.25, r * 0.75, r * 1.25), needles)
    return model.mesh()


def hardwood() -> Mesh:
    """A bottomland hardwood: a short trunk and a broad, rounded crown."""
    model: LowPoly = LowPoly()
    model.cylinder((0, 0, 0), 0.08, 0.95, (104, 76, 52), sides=5)
    for x, y, z, r in [
        (0.0, 1.32, 0.0, 0.62),
        (0.32, 1.12, 0.08, 0.44),
        (-0.3, 1.18, -0.06, 0.48),
        (0.05, 1.05, -0.32, 0.4),
    ]:
        model.blob((x, y, z), (r, r * 0.85, r), LEAVES)
    return model.mesh()


def grass() -> Mesh:
    """A few tufts of wiregrass and old-field grass."""
    model: LowPoly = LowPoly()
    for x, z, h in [
        (-0.22, -0.15, 0.32),
        (0.18, 0.1, 0.38),
        (-0.05, 0.25, 0.28),
        (0.25, -0.25, 0.3),
    ]:
        model.cone((x, 0, z), 0.09, h, (170, 160, 82), sides=5)
    return model.mesh()


def house(firewise: bool) -> Mesh:
    """A small house: walls, a gabled roof, a chimney, a door, and windows.

    Firewise homes get a metal roof and a gravel strip around the walls.
    """
    roof: RGB = (96, 112, 128) if firewise else (162, 84, 58)
    model: LowPoly = LowPoly()
    if firewise:
        model.box((0, 0.01, 0), (0.86, 0.02, 0.74), (176, 172, 164))
    model.box((0, 0.22, 0), (0.62, 0.44, 0.5), (236, 226, 205))
    model.gable_roof((0, 0.44, 0), 0.74, 0.62, 0.3, roof)
    model.box((0.18, 0.66, 0.08), (0.08, 0.22, 0.08), (128, 96, 84))
    model.box((0, 0.13, -0.252), (0.12, 0.24, 0.006), (88, 66, 52))
    for x in (-0.2, 0.2):
        model.box((x, 0.27, -0.252), (0.1, 0.1, 0.006), (160, 200, 222))
    return model.mesh()


def damaged_house() -> Mesh:
    """What is left after a home burns: charred walls without a roof."""
    model: LowPoly = LowPoly()
    model.box((0, 0.12, 0), (0.62, 0.24, 0.5), (70, 60, 54))
    model.box((0.18, 0.3, 0.08), (0.08, 0.36, 0.08), (84, 70, 62))
    return model.mesh()


def stump() -> Mesh:
    """A charred snag left after an intense fire."""
    model: LowPoly = LowPoly()
    model.cylinder((0, 0, 0), 0.06, 0.55, CHAR, sides=5)
    return model.mesh()


def helicopter() -> Mesh:
    """A firefighting helicopter with a water bucket on a long line."""
    model: LowPoly = LowPoly()
    red: RGB = (200, 48, 40)
    model.blob((0, 0, 0), (0.42, 0.3, 0.7), red)
    model.box((0, 0.05, 0.95), (0.08, 0.08, 0.8), red)
    model.box((0, 0.22, 1.32), (0.04, 0.32, 0.16), red)
    model.box((0, 0.34, 0), (1.9, 0.02, 0.12), (40, 40, 44))
    model.box((0, 0.34, 0), (0.12, 0.02, 1.9), (40, 40, 44))
    model.box((0, 0.1, -0.42), (0.36, 0.16, 0.12), (170, 210, 230))
    model.box((0, -0.9, 0), (0.02, 1.2, 0.02), (60, 60, 60))
    model.cylinder((0, -1.75, 0), 0.16, 0.28, (230, 120, 40), sides=6)
    return model.mesh()
