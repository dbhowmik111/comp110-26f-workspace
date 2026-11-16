"""Stage 2: convert logits into probabilities with softmax and normalization."""

__author__: str = "Your PID goes here."

from math import exp


def next_token(logits: dict[int, float]) -> int:
    """Compute probabilities, then make the same greedy choice as stage 1."""
    token_ids: list[int] = list(logits.keys())
    scores: list[float] = list(logits.values())

    # TODO: Choose the token ID with the highest softmax probability; keep the first tie.
    raise NotImplementedError("Complete next_token for this stage.")


def softmax(scores: list[float]) -> list[float]:
    """Exponentiate shifted logits, then normalize the positive weights."""
    # TODO: Implement the softmax calculation described in the README, preserving order.
    raise NotImplementedError("Complete softmax for this stage.")


def normalize(weights: list[float]) -> list[float]:
    """Return probabilities for nonnegative weights with a positive total."""
    # TODO: Return a new list containing each weight's share of the total.
    raise NotImplementedError("Complete normalize for this stage.")


if __name__ == "__main__":
    # TODO: Add calls to check your functions against the examples in the README.
    pass
