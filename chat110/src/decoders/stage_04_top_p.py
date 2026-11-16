"""Stage 4: restrict sampling to a prefix of the ranked probability mass."""

__author__: str = "Your PID goes here."

from math import exp
from random import random, seed

from chat110.support import rank_indices

TOP_P: float = 0.9


def next_token(logits: dict[int, float]) -> int:
    """Compute softmax, filter, and sample an original token ID."""
    token_ids: list[int] = list(logits.keys())
    scores: list[float] = list(logits.values())

    # TODO: Sample a token ID from softmax probabilities filtered using TOP_P.
    raise NotImplementedError("Complete next_token for this stage.")


def softmax(scores: list[float]) -> list[float]:
    """Convert a nonempty list of finite scores into probabilities."""
    # TODO: Reuse your completed softmax function from Stage 3.
    raise NotImplementedError("Complete softmax for this stage.")


def top_p(probabilities: list[float], p: float) -> list[float]:
    """Keep the smallest leading probability prefix reaching p, with 0 < p <= 1."""
    # TODO: Return normalized probabilities for the leading candidates covering p.
    raise NotImplementedError("Complete top_p for this stage.")


def sample_index(probabilities: list[float], draw: float) -> int:
    """Choose a position for a supplied draw, where 0.0 <= draw < 1.0."""
    # TODO: Reuse your completed sample_index function from Stage 3.
    raise NotImplementedError("Complete sample_index for this stage.")


def normalize(weights: list[float]) -> list[float]:
    """Return probabilities for nonnegative weights with a positive total."""
    # TODO: Reuse your completed normalize function from Stage 3.
    raise NotImplementedError("Complete normalize for this stage.")


if __name__ == "__main__":
    # TODO: Add calls to check your functions against the examples in the README.
    pass
