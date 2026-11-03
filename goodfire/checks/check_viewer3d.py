"""Checks that the 3D viewer depends only on protocols, not your classes."""

import ast
import pathlib

import viewer3d

STUDENT_CLASSES: set[str] = {
    "Vegetation",
    "Grass",
    "Pine",
    "Hardwood",
    "Home",
    "Water",
    "Road",
    "Landscape",
    "Wildfire",
    "Cleared",
    "Wind",
    "Slope",
    "FuelMoisture",
    "BurnPlan",
    "FuelBreak",
    "DefensibleSpace",
    "WaterDrop",
    "SeasonPlan",
}


class Shrub:
    """A class no part of the assignment defines. It still gets drawn."""

    def __init__(self, fuel: float, burning: bool):
        """Create a shrub."""
        self.fuel = fuel
        self.burning = burning

    def appearance(self) -> str:
        """Ask to be drawn as a hardwood."""
        return "hardwood"

    def can_ignite(self) -> bool:
        """Unburned shrubs can ignite."""
        return not self.burning

    def ignition_chance(self) -> float:
        """A fixed chance."""
        return 0.5

    def ignite(self) -> None:
        """Start burning."""
        self.burning = True

    def burn(self) -> None:
        """Nothing changes in this tiny stand-in."""

    def is_burning(self) -> bool:
        """Return True while burning."""
        return self.burning


def test_viewer_never_names_student_classes() -> None:
    """The viewer's source mentions none of the student's class names."""
    source: str = pathlib.Path(viewer3d.__file__).read_text()
    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.alias):
            names.add(node.name)
    assert names.isdisjoint(STUDENT_CLASSES)


def test_any_rendered_burnable_gets_a_model() -> None:
    """Model choice comes only from appearance() and the Burnable protocol."""
    assert viewer3d.model_key(Shrub(0.5, burning=False)) == "hardwood"  # type: ignore[arg-type]
    assert viewer3d.plant_state(Shrub(0.5, burning=True)) == "burning"


def test_rows_run_north_to_south_away_from_the_camera() -> None:
    """Row 0 (north, uphill) is farthest from the starting camera."""
    assert viewer3d.world_z(0) > viewer3d.world_z(30)
    assert viewer3d.corner_height(0, 10) > viewer3d.corner_height(30, 10)


def test_colors_from_cells_are_parsed() -> None:
    """A cell's "#RRGGBB" color() string becomes three channels."""
    assert viewer3d.hex_to_rgb("#3F8FC9") == (63, 143, 201)
