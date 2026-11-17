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

    token_ids: list[int] = list(logits.keys())
    scores: list[float] = list(logits.values())

    probabilities: list[float] = softmax(scores)
    ranked_indices: list[int] = rank_indices(probabilities)

    ranked_probabilities: list[float] = []
    index: int
    for index in ranked_indices:
        ranked_probabilities.append(probabilities[index])

    filtered_probabilities: list[float] = top_p(ranked_probabilities, TOP_P)
    sampled_position: int = sample_index(filtered_probabilities, random())
    original_index: int = ranked_indices[sampled_position]
    return token_ids[original_index]


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
    kept: list[float] = []
    running_total: float = 0.0
    probability: float

    for probability in probabilities:
        kept.append(probability)
        running_total = running_total + probability
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
    # TODO: Add calls to check your functions against the examples in the README.
    assert top_p([0.50, 0.30, 0.15, 0.05], 0.70) == [0.625, 0.375]
    assert top_p([0.50, 0.30, 0.15, 0.05], 0.50) == [1.0]

    seed(110)
    assert next_token({42: 0.0, 7: 10.0, 99: -5.0}) == 7
