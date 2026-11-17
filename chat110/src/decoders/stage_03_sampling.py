"""Stage 3: sample a token using cumulative probability intervals."""

__author__: str = "730986400"

from math import exp
from random import random, seed


def next_token(logits: dict[int, float]) -> int:
    """Sample a token ID instead of always taking the largest score."""
    token_ids: list[int] = list(logits.keys())
    scores: list[float] = list(logits.values())

    probabilities: list[float] = softmax(scores)
    draw: float = random()
    chosen_index: int = sample_index(probabilities, draw)
    return token_ids[chosen_index]


def softmax(scores: list[float]) -> list[float]:
    """Convert a nonempty list of finite scores into probabilities."""
    largest_score: float = scores[0]
    score: float
    for score in scores:
        if score > largest_score:
            largest_score = score

    weights: list[float] = []
    for score in scores:
        weights.append(exp(score - largest_score))

    return normalize(weights)


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
    assert sample_index([0.2, 0.3, 0.5], 0.1) == 0
    assert sample_index([0.2, 0.3, 0.5], 0.2) == 1
    assert sample_index([0.2, 0.3, 0.5], 0.5) == 2
    assert sample_index([0.0, 1.0, 0.0], 0.0) == 1
    assert sample_index([0.2, 0.3, 0.5], 0.0) == 0
    assert sample_index([0.2, 0.3, 0.5], 0.4) == 1
    assert sample_index([0.2, 0.3, 0.5], 0.999) == 2
    assert sample_index([0.5, 0.4999999999999998, 0.0], 0.9999999999999999) == 1

    seed(110)
    assert next_token({42: 2.0}) == 42
