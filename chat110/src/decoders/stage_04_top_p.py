"""Stage 4: restrict sampling to a prefix of the ranked probability mass."""

__author__: str = "730986400"

from math import exp
from random import random, seed

from chat110.support import rank_indices

TOP_P: float = 0.9


def next_token(logits: dict[int, float]) -> int:
    """Compute softmax, filter, and sample an original token ID."""
    token_ids: list[int] = list(logits.keys())
    scores: list[float] = list(logits.values())

    probabilities: list[float] = softmax(scores)
    filtered_probabilities: list[float] = top_p(probabilities, TOP_P)
    draw: float = random()
    chosen_index: int = sample_index(filtered_probabilities, draw)
    return token_ids[chosen_index]


def softmax(scores: list[float]) -> list[float]:
    """Convert a nonempty list of finite scores into probabilities."""
    largest_score: float = scores[0]
    score: float
    for score in scores:
        if score > largest_score:
            argest_score = score

    weights: list[float] = []
    for score in scores:
        weights.append(exp(score - largest_score))

    return normalize(weights)


def top_p(probabilities: list[float], p: float) -> list[float]:
    """Keep the smallest leading probability prefix reaching p, with 0 < p <= 1."""
    if p == 1.0:
        return probabilities.copy()

    ranked_indices: list[int] = rank_indices(probabilities)
    kept: list[float] = [0.0] * len(probabilities)
    running_total: float = 0.0
    index: int

    for index in ranked_indices:
        kept[index] = probabilities[index]
        running_total = running_total + probabilities[index]
        if running_total >= p:
            break

    return normalize(kept)


def sample_index(probabilities: list[float], draw: float) -> int:
    """Choose a position for a supplied draw, where 0.0 <= draw < 1.0."""
    running_total: float = 0.0
    last_positive_index: int = 0
    index: int

    for index in range(len(probabilities)):
        probability: float = probabilities[index]
        if probability > 0.0:
            last_positive_index = index

        running_total = running_total + probability
        if draw < running_total:
            return index

    return last_positive_index


def normalize(weights: list[float]) -> list[float]:
    """Return probabilities for nonnegative weights with a positive total."""
    weight_total: float = 0
    weight: float
    for weight in weights:
        weight_total = weight_total + weight

    probabilities: list[float] = []
    for weight in weights:
        probabilities.append(weight / weight_total)
    return probabilities


if __name__ == "__main__":
    example: list[float] = [0.125, 0.5, 0.125, 0.25]

    filtered: list[float] = top_p(example, 0.75)
    assert len(filtered) == len(example)
    assert filtered[0] == 0.0
    assert abs(filtered[1] - 2.0 / 3.0) < 0.000001
    assert filtered[2] == 0.0
    assert abs(filtered[3] - 1.0 / 3.0) < 0.000001

    assert top_p(example, 0.1) == [0.0, 1.0, 0.0, 0.0]
    assert top_p(example, 0.8) == normalize([0.125, 0.5, 0.0, 0.25])

    full: list[float] = top_p(example, 1.0)
    assert full == example
    assert full is not example
    assert example == [0.125, 0.5, 0.125, 0.25]

    seed(110)
    assert next_token({42: 0.0, 7: 10.0, 99: -5.0}) == 7
