"""PROVIDED: the Part 2 simulation, built around your Part 1 Landscape.

Wildfire does not change Landscape. It holds one (composition) and adds
weather, embers, a burn day, management tactics, and a budget. It fits
three protocols at once: Simulation (for the 3D viewer), FireGround (for
tactics and burn plans), and HasWeather (for the viewer's weather report).

A season can open with a burn day: the crew builds the burn plan's control
line, waits for the first day whose forecast fits the prescription, and
lights good fire. When the burn is out, months pass (the burned squares
green up with a light fuel load), and then the wildfire season begins.
"""

from goodfire.burnplan import BurnPlan
from goodfire.burnplan import first_burn_day
from goodfire.dice import Dice
from goodfire.fieldkit import kind_at
from goodfire.grid import Square
from goodfire.landscape import Landscape
from goodfire.part2_protocols import WeatherEffect
from goodfire.plants import Vegetation
from goodfire.protocols import Land
from goodfire.recursion import spot_fire
from goodfire.tactics import FUEL_KEPT
from goodfire.tactics import Cleared
from goodfire.tactics import Tactic
from goodfire.tactics import WaterDrop
from goodfire.weather import FuelMoisture
from goodfire.weather import Slope
from goodfire.weather import Wind

SPOT_CHANCE: float = 0.03
"""Chance per step that a burning square throws an ember in a 10 m/s wind."""

SPOT_DEPTH: int = 2
"""How many hops one ember (and the embers it starts) may make."""

BURN_DAY_STEPS: int = 60
"""A burn day ends after this many steps even if something still burns."""

HABITAT: set[str] = {"pine", "grass"}
"""Fire-adapted kinds of land: good fire here restores habitat."""

BURN_WIND_TOWARD: float = 0.0
"""Forecast winds blow from the south, toward the north (row 0)."""

HOLDING_LIMIT: float = 15.0
"""Wind (m/s) at which a holding crew can no longer catch spot fires."""


class Wildfire:
    """A fire season: a landscape, its weather, and the crew's plan."""

    landscape: Landscape
    effects: list[WeatherEffect]
    budget: int
    seed: int
    dice: Dice
    steps: int
    spent: int
    scheduled: list[Tactic]
    soaked: dict[Square, int]
    spot_fires: int
    drops: list[tuple[float, float, float]]
    phase: str
    season_effects: list[WeatherEffect]
    fire_starts: list[Square]
    burn_steps: int
    burn_day: int
    burn_area: set[Square]
    good_fire: set[Square]
    off_target: set[Square]
    note: str

    def __init__(
        self,
        landscape: Landscape,
        effects: list[WeatherEffect],
        budget: int,
        seed: int,
    ):
        """Wrap a landscape and set the weather and the budget.

        Args:
            landscape: A Part 1 landscape; its squares become the map.
            effects: Weather and terrain effects for the wildfire season,
                applied in this order.
            budget: Dollars available for the burn and tactics this season.
            seed: The random seed for spreading and embers.
        """
        self.landscape = landscape
        self.effects = effects
        self.budget = budget
        self.seed = seed
        self.dice = Dice(seed)
        self.steps = 0
        self.spent = 0
        self.scheduled = []
        self.soaked = {}
        self.spot_fires = 0
        self.drops = []
        self.phase = "season"
        self.season_effects = effects
        self.fire_starts = []
        self.burn_steps = 0
        self.burn_day = -1
        self.burn_area = set()
        self.good_fire = set()
        self.off_target = set()
        self.note = ""

    def __str__(self) -> str:
        """Summarize the burn day or the season for the status line."""
        if self.phase == "burn day":
            return (
                f"Burn day (day {self.burn_day + 1} of the window), "
                f"step {self.burn_steps}: "
                f"{self.landscape.count_burning()} burning, "
                f"{len(self.good_fire)} squares of good fire, "
                f"{len(self.off_target)} off target"
            )
        return (
            f"Step {self.steps}: {self.landscape.count_burning()} burning, "
            f"{round(self.landscape.burned_fraction() * 100)}% burned, "
            f"{self.homes_safe()} of {self.homes_total()} homes safe, "
            f"{self.spot_fires} spot fires"
        )

    def __repr__(self) -> str:
        """Show the main ingredients of this simulation."""
        return (
            f"Wildfire({self.landscape!r}, effects={self.effects!r}, "
            f"budget={self.budget}, seed={self.seed})"
        )

    # -------------------------------------------- Simulation protocol

    def cell_at(self, row: int, col: int) -> Land:
        """Return the object on one square."""
        return self.landscape.cell_at(row, col)

    def ignite(self, row: int, col: int) -> bool:
        """Set one square on fire if it can burn.

        On a burn day, the holding crew patrols outside the burn area and
        puts out most new fires there before they spread.
        """
        if self.phase == "burn day" and Square(row, col) not in self.burn_area:
            if self.dice.roll() < self.holding_catch():
                return False
        return self.landscape.ignite(row, col)

    def step(self) -> None:
        """Advance the burn day or the season by one step."""
        if self.phase == "burn day":
            self._spread()
            self.burn_steps += 1
            self._tally_burn()
            if self.is_out() or self.burn_steps >= BURN_DAY_STEPS:
                self._end_burn_day()
            return
        self.drops = []
        tactic: Tactic
        for tactic in self.scheduled:
            if tactic.when() > 0 and tactic.when() == self.steps:
                tactic.apply(self)
                if isinstance(tactic, WaterDrop):
                    self.drops.append(
                        (tactic.center.row, tactic.center.col, tactic.radius)
                    )
        self.spot_fires += self._spread()
        self._dry_out()
        self.steps += 1

    # -------------------------------------------- FireGround protocol

    def replace(self, row: int, col: int, cell: Land) -> None:
        """Put a new object on one square."""
        self.landscape.grid[row][col] = cell

    def wet(self, row: int, col: int, steps: int) -> None:
        """Soak one square so no fire spreads into it for some steps."""
        square: Square = Square(row, col)
        self.soaked[square] = max(self.soaked.get(square, 0), steps)

    # -------------------------------------------- the burn day

    def plan_burn(
        self, burn: BurnPlan, forecasts: list[dict[str, float]]
    ) -> bool:
        """Get ready to burn on the first forecast day in prescription.

        Builds the control line, charges the budget, sets the burn-day
        weather, and lights the ignition squares inside the burn area.

        Args:
            burn: The burn plan.
            forecasts: One weather forecast per day of the burn window.

        Returns:
            True if a burn day is set; False if no day fit the
            prescription or the burn would cost more than the budget.
        """
        day: int = first_burn_day(forecasts, burn.prescription)
        if day == -1:
            self.note = "No day in the burn window fit the prescription."
            return False
        price: int = burn.cost(self)
        if self.spent + price > self.budget:
            self.note = f"The burn would cost ${price:,}, over the budget."
            return False
        area: set[Square] = burn.area(self)
        square: Square
        for square in burn.line(self):
            cell: Land = self.cell_at(square.row, square.col)
            if cell.is_fuel() and not cell.is_home():
                self.replace(
                    square.row, square.col, Cleared(square.row, square.col)
                )
        self.spent += price
        self.burn_day = day
        self.burn_area = area
        forecast: dict[str, float] = forecasts[day]
        self.effects = [
            Slope(),
            Wind(forecast["wind"], BURN_WIND_TOWARD),
            FuelMoisture(forecast["moisture"]),
        ]
        self.phase = "burn day"
        for square in burn.ignition.squares():
            if square in area:
                self.ignite(square.row, square.col)
        self.note = f"Burn day {day + 1} of the window"
        if self.is_out():
            self._end_burn_day()
        return True

    def holding_catch(self) -> float:
        """Return the chance the holding crew catches one spot fire.

        Calm air lets the crew catch nearly every spot fire; the stronger
        the wind, the faster a spot fire grows and the harder it is to catch.
        """
        wind: Wind | None = self.wind()
        if wind is None:
            return 1.0
        return max(0.0, 1.0 - wind.speed / HOLDING_LIMIT)

    def _tally_burn(self) -> None:
        """Sort every square the burn has touched: good fire or not."""
        row: int = 0
        while row < len(self.landscape.grid):
            col: int = 0
            while col < len(self.landscape.grid[row]):
                cell: Land = self.cell_at(row, col)
                if cell.is_fuel() and not cell.can_ignite():
                    square: Square = Square(row, col)
                    if (
                        square in self.burn_area
                        and kind_at(self, square) in HABITAT
                    ):
                        self.good_fire.add(square)
                    else:
                        self.off_target.add(square)
                col += 1
            row += 1

    def _end_burn_day(self) -> None:
        """Put out the burn, let months pass, and start the season."""
        self._tally_burn()
        cells: list[Land]
        for cells in self.landscape.grid:
            cell: Land
            for cell in cells:
                if isinstance(cell, Vegetation) and cell.state != "unburned":
                    cell.state = "unburned"
                    cell.time_left = 0
                    cell.fuel = round(cell.fuel * FUEL_KEPT, 2)
        self.begin_season()

    def begin_season(self) -> None:
        """Switch to the season's weather and light the season's fires."""
        self.phase = "season"
        self.effects = self.season_effects
        square: Square
        for square in self.fire_starts:
            self.ignite(square.row, square.col)

    # -------------------------------------------- planning and spreading

    def schedule(self, tactic: Tactic) -> bool:
        """Add a tactic if the budget allows; act now if it is pre-season.

        Returns:
            True if the tactic fit in the budget.
        """
        price: int = tactic.cost(self)
        if self.spent + price > self.budget:
            return False
        self.spent += price
        self.scheduled.append(tactic)
        if tactic.when() == 0:
            tactic.apply(self)
        return True

    def spread_chance(self, source: Land, target: Land) -> float:
        """Return the chance fire spreads from source into target.

        Start from the target's own ignition chance, then let each weather
        effect adjust it in order. Unburnable and soaked squares get 0.0.
        """
        if not target.is_fuel():
            return 0.0
        if Square(target.row, target.col) in self.soaked:
            return 0.0
        chance: float = target.ignition_chance()
        effect: WeatherEffect
        for effect in self.effects:
            chance = effect.adjust(source, target, chance)
        return min(max(chance, 0.0), 1.0)

    def _spread(self) -> int:
        """Spread flames and throw embers for one step.

        Returns:
            How many spot fires embers started.
        """
        effect: WeatherEffect
        for effect in self.effects:
            effect.advance()
        wind: Wind | None = self.wind()
        to_ignite: list[Land] = []
        launch_sites: list[Square] = []
        cells: list[Land]
        for cells in self.landscape.grid:
            cell: Land
            for cell in cells:
                if not cell.is_burning():
                    continue
                neighbor: Land
                for neighbor in self.landscape.neighbors(cell.row, cell.col):
                    if self._catches(cell, neighbor):
                        to_ignite.append(neighbor)
                cell.burn()
                if wind is not None and self.dice.roll() < (
                    SPOT_CHANCE * wind.speed / 10.0
                ):
                    launch_sites.append(Square(cell.row, cell.col))
        target: Land
        for target in to_ignite:
            if target.can_ignite():
                target.ignite()
        started: int = 0
        site: Square
        for site in launch_sites:
            if wind is not None:
                started += spot_fire(
                    self, site.row, site.col, wind, self.dice, SPOT_DEPTH
                )
        return started

    def _catches(self, source: Land, target: Land) -> bool:
        """Roll the dice for one neighbor of a burning square."""
        if not target.can_ignite():
            return False
        return self.dice.roll() < self.spread_chance(source, target)

    def _dry_out(self) -> None:
        """Count down soaked squares; remove the ones that have dried."""
        dried: list[Square] = []
        square: Square
        for square in self.soaked:
            self.soaked[square] -= 1
            if self.soaked[square] <= 0:
                dried.append(square)
        for square in dried:
            del self.soaked[square]

    def wind(self) -> Wind | None:
        """Return the first Wind in the weather, or None if it is calm."""
        effect: WeatherEffect
        for effect in self.effects:
            if isinstance(effect, Wind):
                return effect
        return None

    # -------------------------------------------- results

    def homes_total(self) -> int:
        """Return how many homes are on the map."""
        return self.landscape.homes_total()

    def homes_safe(self) -> int:
        """Return how many homes have not caught fire."""
        return self.landscape.homes_safe()

    def habitat_restored(self) -> int:
        """Return how many squares of habitat got good fire this season."""
        return len(self.good_fire)

    def is_out(self) -> bool:
        """Return True when nothing is burning."""
        return self.landscape.count_burning() == 0

    def is_over(self) -> bool:
        """Return True when the burn is done and the wildfire is out."""
        return self.phase == "season" and self.is_out()

    # -------------------------------------------- HasWeather protocol

    def weather_report(self) -> str:
        """Return one line describing every weather effect."""
        parts: list[str] = []
        effect: WeatherEffect
        for effect in self.effects:
            parts.append(effect.describe())
        return "Weather: " + ", ".join(parts)

    def water_drops(self) -> list[tuple[float, float, float]]:
        """Return (row, col, radius) for each water drop made this step."""
        return list(self.drops)
