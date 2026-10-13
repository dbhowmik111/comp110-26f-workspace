"""PROVIDED: the dice behind the fire, seeded so every run can repeat.

The same seed always gives the same rolls, so the same sketch and the same
ignitions always grow the same landscape and burn the same way.
"""

import random


class Dice:
    """A seeded source of random numbers for one landscape."""

    rng: random.Random

    def __init__(self, seed: int):
        """Create dice that always roll the same way for the same seed.

        Args:
            seed: Any whole number.
        """
        self.rng = random.Random(seed)

    def roll(self) -> float:
        """Return a random number from 0.0 up to (not including) 1.0."""
        return self.rng.random()

    def fuel_load(self, low: float, high: float) -> float:
        """Return a random fuel load from low to high, to two decimals."""
        return round(self.rng.uniform(low, high), 2)
