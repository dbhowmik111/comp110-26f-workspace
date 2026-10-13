"""Checks for Part 1: classes, magic methods, inheritance, and protocols.

Run with:  uv run python -m pytest checks
The Gradescope autograder checks the same behavior (and a little more).
"""

import pytest

from goodfire import science
from goodfire.cover import Home
from goodfire.cover import Road
from goodfire.cover import Water
from goodfire.grid import Point
from goodfire.grid import Square
from goodfire.landscape import Landscape
from goodfire.plants import Grass
from goodfire.plants import Hardwood
from goodfire.plants import Pine
from goodfire.plants import Vegetation
from goodfire.protocols import Burnable
from goodfire.protocols import Feature
from goodfire.sketch import Polygon
from goodfire.sketch import Polyline


def homes() -> Polygon:
    """Return the 24-home neighborhood from the default sketch."""
    return Polygon(
        [
            Point(2.0, 11.0),
            Point(2.0, 19.0),
            Point(5.0, 19.0),
            Point(5.0, 11.0),
        ],
        "homes",
    )


# ----------------------------------------------------------- land cover


def test_vegetation_leaves_specifics_to_each_plant() -> None:
    """Vegetation only describes a family; each plant overrides name()."""
    with pytest.raises(NotImplementedError):
        Vegetation(0, 0, 0.5).name()


def test_plants_share_one_str_and_repr() -> None:
    """Each plant fills in its name; Vegetation formats the sentence."""
    assert (
        str(Pine(4, 12, 0.85))
        == "Longleaf pine at row 4, column 12: 85% fuel, unburned"
    )
    assert (
        str(Grass(1, 2, 0.4)) == "Grass at row 1, column 2: 40% fuel, unburned"
    )
    assert repr(Hardwood(3, 7, 0.75)) == "Hardwood(row=3, col=7, fuel=0.75)"


def test_longleaf_survives_a_surface_fire() -> None:
    """Pine adds to the shared __str__ with super()."""
    pine: Pine = Pine(0, 0, 0.5)
    pine.ignite()
    assert (
        str(pine)
        == "Longleaf pine at row 0, column 0: 50% fuel, burning (2 steps left)"
    )
    pine.burn()
    pine.burn()
    assert (
        str(pine) == "Longleaf pine at row 0, column 0: 50% fuel, burned"
        " (the longleaf survived)"
    )


def test_each_fuel_burns_for_its_own_time() -> None:
    """Grass flashes, pine burns two steps, hardwood litter smolders three."""
    for plant, steps in (
        (Grass(0, 0, 0.5), 1),
        (Pine(0, 0, 0.5), 2),
        (Hardwood(0, 0, 0.5), 3),
    ):
        plant.ignite()
        for _step in range(steps):
            assert plant.is_burning()
            plant.burn()
        assert not plant.is_burning()
        assert not plant.can_ignite()


def test_ignition_chance_follows_the_model() -> None:
    """p = P_H * (1 + p_veg) * (1 + p_den); fuel 0.0 is sparse, 1.0 dense."""
    assert science.density_factor(0.0) == pytest.approx(0.6)
    assert science.density_factor(1.0) == pytest.approx(1.3)
    assert Grass(0, 0, 0.5).ignition_chance() == pytest.approx(
        science.P_H * 1.4 * 0.95
    )
    assert Pine(0, 0, 1.0).ignition_chance() == pytest.approx(science.P_H * 1.3)
    assert Hardwood(0, 0, 0.5).ignition_chance() == pytest.approx(
        science.P_H * 0.6 * 0.95
    )


def test_homes_and_firewise_homes() -> None:
    """A Firewise home is much harder to ignite, and says so."""
    plain: Home = Home(2, 11, False)
    hardened: Home = Home(2, 12, True)
    assert str(plain) == "Home at row 2, column 11: safe"
    assert str(hardened) == "Home at row 2, column 12 (Firewise): safe"
    assert repr(hardened) == "Home(row=2, col=12, hardened=True)"
    assert hardened.ignition_chance() < plain.ignition_chance()


def test_home_catches_burns_and_is_damaged() -> None:
    """A safe home ignites, burns for four steps, then cannot catch again."""
    home: Home = Home(2, 11, False)
    assert home.can_ignite()
    assert not home.is_burning()
    home.ignite()
    assert home.is_burning()
    assert not home.can_ignite()
    assert str(home) == "Home at row 2, column 11: on fire (4 steps left)"
    for _ in range(4):
        home.burn()
    assert not home.is_burning()
    assert not home.can_ignite()
    assert str(home) == "Home at row 2, column 11: damaged"


def test_water_and_roads_never_burn() -> None:
    """Water and roads answer every fire question with "no"."""
    for solid in (Water(0, 0), Road(0, 0)):
        assert not solid.is_fuel()
        assert not solid.is_home()
        assert not solid.can_ignite()
        assert solid.ignition_chance() == 0.0
        solid.ignite()
        assert not solid.is_burning()
    assert Home(0, 0, False).is_fuel()
    assert Home(0, 0, False).is_home()


def test_protocol_membership() -> None:
    """Plants and homes fit Burnable; water and roads do not."""
    for burnable in (
        Grass(0, 0, 0.5),
        Pine(0, 0, 0.5),
        Hardwood(0, 0, 0.5),
        Home(0, 0, False),
    ):
        assert isinstance(burnable, Burnable)
    for solid in (Water(0, 0), Road(0, 0)):
        assert not isinstance(solid, Burnable)


def test_repr_round_trips() -> None:
    """repr() is Python that rebuilds an equivalent object."""
    namespace: dict[str, object] = {
        "Grass": Grass,
        "Pine": Pine,
        "Hardwood": Hardwood,
        "Home": Home,
        "Water": Water,
        "Road": Road,
    }
    for original in (
        Pine(3, 7, 0.75),
        Home(1, 1, True),
        Water(8, 3),
        Road(5, 5),
    ):
        assert repr(eval(repr(original), namespace)) == repr(original)


# ----------------------------------------------------------- sketch shapes


def test_polygon_contains_and_squares() -> None:
    """A rectangle from (2, 11) to (5, 19) covers 3 rows x 8 columns."""
    assert homes().contains(3.5, 15.5)
    assert not homes().contains(6.5, 15.5)
    assert len(homes().squares()) == 24
    assert homes().squares()[0] == Square(2, 11)
    assert str(homes()) == "homes area with 4 corners covering 24 squares"


def test_triangle_polygon() -> None:
    """Ray casting works for slanted edges too."""
    triangle: Polygon = Polygon(
        [Point(0.0, 0.0), Point(10.0, 0.0), Point(0.0, 10.0)], "pond"
    )
    assert triangle.contains(2.5, 2.5)
    assert not triangle.contains(8.5, 8.5)


def test_polyline_squares_and_length() -> None:
    """A 10-square line ending on an edge touches 11 squares; it is 300 m."""
    road: Polyline = Polyline([Point(5.5, 0.0), Point(5.5, 10.0)], "road")
    assert road.length() == pytest.approx(10.0)
    assert road.squares()[:3] == [Square(5, 0), Square(5, 1), Square(5, 2)]
    assert str(road) == "road line 300 m long covering 11 squares"


def test_shapes_fit_feature_and_round_trip() -> None:
    """Shapes fit the Feature protocol, and their reprs rebuild them."""
    road: Polyline = Polyline([Point(5.5, 0.0), Point(5.5, 10.0)], "road")
    for shape in (homes(), road):
        assert isinstance(shape, Feature)
    rebuilt: object = eval(repr(homes()), {"Polygon": Polygon, "Point": Point})
    assert repr(rebuilt) == repr(homes())


# ----------------------------------------------------------- landscape


def test_landscape_applies_features() -> None:
    """Sketched homes replace the base cover; the repr records the sketch."""
    land: Landscape = Landscape(110, [homes()])
    assert land.homes_total() == 24
    assert isinstance(land.cell_at(3, 15), Home)
    assert (
        str(land) == "Step 0: 0 burning, 0% of fuel burned, 24 of 24 homes safe"
    )
    assert repr(land).startswith("Landscape(seed=110, features=[Polygon(")


def test_unknown_cover_is_rejected() -> None:
    """A typo in a cover name raises ValueError instead of failing silently."""
    with pytest.raises(ValueError):
        Landscape(
            110,
            [
                Polygon(
                    [Point(0.0, 0.0), Point(0.0, 3.0), Point(3.0, 3.0)], "lava"
                )
            ],
        )


def test_neighbors_and_ignite() -> None:
    """Edges have fewer neighbors; water cannot burn."""
    land: Landscape = Landscape(
        110, [Polyline([Point(9.5, 0.0), Point(9.5, 30.0)], "river")]
    )
    assert len(land.neighbors(0, 0)) == 2
    assert len(land.neighbors(15, 15)) == 4
    assert not land.ignite(9, 4)
    assert land.ignite(22, 7)
    assert land.count_burning() == 1


def test_fire_is_repeatable_and_spreads() -> None:
    """Two landscapes with the same seed burn the same way."""
    first: Landscape = Landscape(110, [homes()])
    second: Landscape = Landscape(110, [homes()])
    for land in (first, second):
        land.ignite(22, 7)
        for _step in range(20):
            land.step()
    assert str(first) == str(second)
    assert first.burned_fraction() > 0.0
