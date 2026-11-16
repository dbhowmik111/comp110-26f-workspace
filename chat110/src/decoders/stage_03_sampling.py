"""Stage 3: sample a token using cumulative probability intervals."""

__author__: str = "Your PID goes here."

from math import exp
from random import random, seed


def next_token(logits: dict[int, float]) -> int:
    """Sample a token ID instead of always taking the largest score."""
    token_ids: list[int] = list(logits.keys())
    scores: list[float] = list(logits.values())

    # TODO: Sample a token ID according to softmax probabilities using one fresh draw.
    raise NotImplementedError("Complete next_token for this stage.")


def softmax(scores: list[float]) -> list[float]:
    """Convert a nonempty list of finite scores into probabilities."""
    # TODO: Reuse your completed softmax function from Stage 2.
    raise NotImplementedError("Complete softmax for this stage.")


def sample_index(probabilities: list[float], draw: float) -> int:
    """Choose a position for a supplied draw, where 0.0 <= draw < 1.0."""
    # TODO: Return the position whose probability interval contains the supplied draw.
    raise NotImplementedError("Complete sample_index for this stage.")


def normalize(weights: list[float]) -> list[float]:
    """Return probabilities for nonnegative weights with a positive total."""
    # TODO: Reuse your completed normalize function from Stage 2.
    raise NotImplementedError("Complete normalize for this stage.")


if __name__ == "__main__":
    # TODO: Add calls to check your functions against the examples in the README.
    pass
