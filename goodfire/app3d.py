"""PROVIDED: run the fire season in 3D.

Run from this folder with:  uv run python app3d.py
Options:
  --plan B         watch plan B instead of the plan chosen in plan.py
  --no-plan        watch the same season with no plan at all
  --hotter-drier   use the hotter, drier climate scenario
"""

# Ursina's type hints are incomplete: it accepts plain tuples where its hints
# say Vec3, and it sets time.dt while running. Only the provided 3D files
# relax checking; your own files keep strict checking.
# pyright: basic, reportArgumentType=false, reportAttributeAccessIssue=false

import sys

# Load Qt (through comp110_gui) before the 3D engine. On Windows the 3D
# engine's bundled C++ runtime DLL would otherwise load first, and Qt then
# crashes while starting up (exit code 0xC0000005).
import comp110_gui  # noqa: F401  (must stay above the ursina imports)
from ursina import Entity
from ursina import Ursina

from goodfire import plan as chosen
from goodfire import scenario
from goodfire.plans import PLANS
from goodfire.plans import SeasonPlan
from goodfire.simulation import Wildfire
from viewer3d import ForestViewer3D

SEED: int = 1


def new_simulation() -> Wildfire:
    """Build the standard season with the options from the command line."""
    climate: str = "historical"
    if "--hotter-drier" in sys.argv:
        climate = "hotter_drier"
    name: str = chosen.CHOSEN_PLAN
    if "--plan" in sys.argv[:-1]:
        name = sys.argv[sys.argv.index("--plan") + 1].upper()
    plan: SeasonPlan | None = None
    if name in PLANS and "--no-plan" not in sys.argv:
        plan = SeasonPlan(name)
    return scenario.build(SEED, climate, plan)


def main() -> None:
    """Open the 3D window and let the season play out."""
    app: Ursina = Ursina(
        title="Good Fire",
        size=(1280, 800),
        development_mode=False,
    )
    viewer: ForestViewer3D = ForestViewer3D(new_simulation, steps_per_second=3)
    driver: Entity = Entity()
    driver.update = viewer.update
    driver.input = viewer.input
    app.run()


if __name__ == "__main__":
    main()
