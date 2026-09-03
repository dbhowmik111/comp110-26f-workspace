"""Pure builders for beam ribbons and translucent planar fills."""

from __future__ import annotations

from dataclasses import dataclass

from spacepaint.world import BeamStroke, FillRegion, Vec3, beam_sample_alpha

RGBA = tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class TrailMeshData:
    vertices: tuple[Vec3, ...]
    triangles: tuple[int, ...]
    colors: tuple[RGBA, ...]


@dataclass(frozen=True, slots=True)
class FillMeshData:
    vertices: tuple[Vec3, ...]
    triangles: tuple[int, ...]


def _brighten(
    color: tuple[float, float, float], amount: float
) -> tuple[float, float, float]:
    return tuple(channel + (1.0 - channel) * amount for channel in color)  # type: ignore[return-value]


def _side_vectors(direction: Vec3) -> tuple[Vec3, Vec3]:
    reference = Vec3(0.0, 0.0, 1.0) if abs(direction.z) < 0.85 else Vec3(0.0, 1.0, 0.0)
    first = direction.cross(reference).normalized()
    second = direction.cross(first).normalized()
    return first, second


def build_trail_mesh(
    strokes: tuple[BeamStroke, ...],
    now: float,
    *,
    width_scale: float = 1.0,
    alpha_scale: float = 1.0,
    whiten: float = 0.0,
) -> TrailMeshData:
    """Build two double-sided, perpendicular ribbons for each visible segment."""
    vertices: list[Vec3] = []
    triangles: list[int] = []
    colors: list[RGBA] = []
    for stroke in strokes:
        rgb = _brighten(stroke.style.color, whiten)
        half_width = stroke.style.width * width_scale / 2
        for start_sample, end_sample in zip(
            stroke.samples, stroke.samples[1:], strict=False
        ):
            segment = end_sample.position - start_sample.position
            if segment.length <= 1e-9:
                continue
            start_alpha = (
                beam_sample_alpha(start_sample, stroke.style, now) * alpha_scale
            )
            end_alpha = beam_sample_alpha(end_sample, stroke.style, now) * alpha_scale
            if start_alpha <= 0 and end_alpha <= 0:
                continue
            first_side, second_side = _side_vectors(segment.normalized())
            for side in (first_side, second_side):
                offset = side * half_width
                base = len(vertices)
                vertices.extend(
                    (
                        start_sample.position - offset,
                        start_sample.position + offset,
                        end_sample.position + offset,
                        end_sample.position - offset,
                    )
                )
                triangles.extend(
                    (
                        base,
                        base + 1,
                        base + 2,
                        base,
                        base + 2,
                        base + 3,
                        base + 2,
                        base + 1,
                        base,
                        base + 3,
                        base + 2,
                        base,
                    )
                )
                colors.extend(
                    (
                        (*rgb, start_alpha),
                        (*rgb, start_alpha),
                        (*rgb, end_alpha),
                        (*rgb, end_alpha),
                    )
                )
    return TrailMeshData(tuple(vertices), tuple(triangles), tuple(colors))


def _project_to_plane(vertex: Vec3, normal: Vec3) -> tuple[float, float]:
    dominant = max(
        ((abs(normal.x), "x"), (abs(normal.y), "y"), (abs(normal.z), "z")),
        key=lambda item: item[0],
    )[1]
    if dominant == "x":
        return vertex.y, vertex.z
    if dominant == "y":
        return vertex.x, vertex.z
    return vertex.x, vertex.y


def _cross_2d(
    first: tuple[float, float],
    second: tuple[float, float],
    third: tuple[float, float],
) -> float:
    return (second[0] - first[0]) * (third[1] - first[1]) - (second[1] - first[1]) * (
        third[0] - first[0]
    )


def _inside_triangle(
    point: tuple[float, float],
    first: tuple[float, float],
    second: tuple[float, float],
    third: tuple[float, float],
    orientation: float,
) -> bool:
    tolerance = 1e-9
    return all(
        orientation * cross >= -tolerance
        for cross in (
            _cross_2d(first, second, point),
            _cross_2d(second, third, point),
            _cross_2d(third, first, point),
        )
    )


def build_fill_mesh(region: FillRegion) -> FillMeshData:
    """Triangulate one simple planar region, including concave outlines."""
    vertices: list[Vec3] = []
    for vertex in region.vertices:
        if not vertices or (vertices[-1] - vertex).length > 1e-9:
            vertices.append(vertex)
    if len(vertices) > 1 and (vertices[0] - vertices[-1]).length <= 1e-9:
        vertices.pop()
    if len(vertices) < 3:
        return FillMeshData((), ())

    normal = region.plane_normal
    if normal is None:
        base = vertices[0]
        for index in range(1, len(vertices) - 1):
            candidate = (vertices[index] - base).cross(vertices[index + 1] - base)
            if candidate.length > 1e-9:
                normal = candidate.normalized()
                break
    if normal is None:
        return FillMeshData((), ())

    points = [_project_to_plane(vertex, normal) for vertex in vertices]
    changed = True
    while changed and len(vertices) > 3:
        changed = False
        for index in range(len(vertices)):
            previous = (index - 1) % len(vertices)
            following = (index + 1) % len(vertices)
            if (
                abs(_cross_2d(points[previous], points[index], points[following]))
                <= 1e-9
            ):
                vertices.pop(index)
                points.pop(index)
                changed = True
                break

    signed_area = sum(
        point[0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * point[1]
        for index, point in enumerate(points)
    )
    if abs(signed_area) <= 1e-9:
        return FillMeshData((), ())
    orientation = 1.0 if signed_area > 0 else -1.0
    remaining = list(range(len(vertices)))
    triangles: list[int] = []
    while len(remaining) > 3:
        ear_found = False
        for offset, current in enumerate(remaining):
            previous = remaining[offset - 1]
            following = remaining[(offset + 1) % len(remaining)]
            if (
                orientation
                * _cross_2d(points[previous], points[current], points[following])
                <= 1e-9
            ):
                continue
            if any(
                _inside_triangle(
                    points[candidate],
                    points[previous],
                    points[current],
                    points[following],
                    orientation,
                )
                for candidate in remaining
                if candidate not in (previous, current, following)
            ):
                continue
            triangles.extend((previous, current, following))
            remaining.pop(offset)
            ear_found = True
            break
        if not ear_found:
            triangles = [
                item
                for index in range(1, len(vertices) - 1)
                for item in (0, index, index + 1)
            ]
            return FillMeshData(tuple(vertices), tuple(triangles))
    triangles.extend(remaining)
    return FillMeshData(tuple(vertices), tuple(triangles))
