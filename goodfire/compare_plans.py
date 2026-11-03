"""PROVIDED: compare the season plans without opening any window.

Run from this folder with:  uv run python compare_plans.py
Every plan faces the same seeds in both climates, so scores are comparable.
Add a plan's letter to see each season for that plan:
    uv run python compare_plans.py D
"""

import sys
from collections.abc import Callable

from goodfire import burnplan
from goodfire import plan
from goodfire import scenario
from goodfire.burnplan import count
from goodfire.fieldkit import kind_at
from goodfire.grid import Square
from goodfire.plans import PLANS
from goodfire.plans import SeasonPlan
from goodfire.simulation import Wildfire

SEEDS: list[int] = [1, 2, 3, 4, 5]


def seasons(choice: SeasonPlan | None) -> list[Wildfire]:
    """Run every seed in both climates with one plan (or none)."""
    runs: list[Wildfire] = []
    for climate in scenario.CLIMATES:
        for seed in SEEDS:
            runs.append(
                scenario.run_to_end(scenario.build(seed, climate, choice))
            )
    return runs


def off_target_kinds(sim: Wildfire) -> dict[str, int]:
    """Count what burned off target on the burn day, by kind of land."""
    return count([kind_at(sim, square) for square in sim.off_target])


def homes_burned_on_burn_days(sim: Wildfire) -> int:
    """Count the homes that caught fire on the burn day."""
    return off_target_kinds(sim).get("home", 0)


def summary(label: str, runs: list[Wildfire]) -> str:
    """One row of totals over all the seasons."""
    habitat: int = sum(sim.habitat_restored() for sim in runs)
    burned: int = sum(homes_burned_on_burn_days(sim) for sim in runs)
    off: int = sum(len(sim.off_target) for sim in runs)
    burns: int = sum(1 for sim in runs if sim.burn_day >= 0)
    safe: int = sum(sim.homes_safe() for sim in runs)
    total: int = sum(sim.homes_total() for sim in runs)
    return (
        f"{label:<12} {habitat:>9}  {burns:>2}/10  {burned:>10}  {off:>10}"
        f"  {safe:>3} of {total}"
    )


def details(name: str) -> None:
    """Print every season for one plan."""
    choice: SeasonPlan = SeasonPlan(name)
    print(choice)
    print(
        "climate       seed  burn day  good fire  off target  homes safe  spent"
    )
    for sim, (climate, seed) in zip(
        seasons(choice),
        [(c, s) for c in scenario.CLIMATES for s in SEEDS],
        strict=True,
    ):
        day: str = "none"
        if sim.burn_day >= 0:
            day = f"day {sim.burn_day + 1}"
        print(
            f"{climate:<13} {seed:>4}  {day:>8}  {sim.habitat_restored():>9}"
            f"  {len(sim.off_target):>10}  {sim.homes_safe():>4} of"
            f" {sim.homes_total()}  ${sim.spent:,}"
        )
        if sim.burn_day < 0 and sim.note:
            print(f"{'':<20}{sim.note}")
        kinds: dict[str, int] = off_target_kinds(sim)
        if kinds:
            listed: str = ", ".join(f"{n} {kind}" for kind, n in kinds.items())
            print(f"{'':<20}off target: {listed}")


def unfinished() -> list[str]:
    """Return the burnplan.py functions that still raise NotImplementedError."""
    a: Square = Square(0, 0)
    tries: dict[str, Callable[[], object]] = {
        "count": lambda: burnplan.count([]),
        "group_by_kind": lambda: burnplan.group_by_kind({}),
        "in_prescription": lambda: burnplan.in_prescription({}, {}),
        "first_burn_day": lambda: burnplan.first_burn_day([], {}),
        "spread_once": lambda: burnplan.spread_once(set(), {a}, {a: []}),
    }
    missing: list[str] = []
    for name, attempt in tries.items():
        try:
            attempt()
        except NotImplementedError:
            missing.append(name)
    return missing


def main() -> None:
    """Compare every plan over ten seasons, or show one plan in detail."""
    missing: list[str] = unfinished()
    if missing:
        print(
            "compare_plans.py needs all five functions in burnplan.py, because "
            "plans A-D are built with them (Step 1 of PART2.md).\n"
            f"Still to write: {', '.join(missing)}.\n"
            "Check each one as you go with: uv run python -m pytest checks"
        )
        sys.exit(1)
    if len(sys.argv) > 1:
        details(sys.argv[1].upper())
        return
    print("Ten seasons (5 seeds x 2 climates) for each plan:\n")
    print("             good fire   burns    burn-day    burn-day  homes safe")
    print("plan         (squares)          homes lost  off target  at the end")
    print(summary("no plan", seasons(None)))
    name: str
    for name in PLANS:
        print(summary(f"{name}", seasons(SeasonPlan(name))))
    print()
    for name in PLANS:
        print(f"{name}: {PLANS[name]}")
    print()
    if plan.CHOSEN_PLAN in PLANS:
        print(f"Your choice in plan.py: {SeasonPlan(plan.CHOSEN_PLAN)}")
    else:
        print(
            f"plan.py's CHOSEN_PLAN is {plan.CHOSEN_PLAN!r}; set it to one of "
            f"{', '.join(PLANS)}."
        )


if __name__ == "__main__":
    main()
