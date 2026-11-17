"""Stage 2: convert logits into probabilities with softmax and normalization."""

__author__: str = "730986400"

from math import exp


def next_token(logits: dict[int, float]) -> int:
    """Compute probabilities, then make the same greedy choice as stage 1."""
    token_ids: list[int] = list(logits.keys())
    scores: list[float] = list(logits.values())

    probabilities: list[float] = softmax(scores)
    best_index: int = 0
    index: int
    for index in range(1, len(probabilities)):
        if probabilities[index] > probabilities[best_index]:
            best_index = index

    return token_ids[best_index]


def softmax(scores: list[float]) -> list[float]:
    """Exponentiate shifted logits, then normalize the positive weights."""
    largest_score: float = scores[0]
    score: float
    for score in scores:
        if score > largest_score:
            largest_score = score

    weights: list[float] = []
    for score in scores:
        weights.append(exp(score - largest_score))

    return normalize(weights)


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
    assert normalize([2.0, 3.0, 5.0]) == [0.2, 0.3, 0.5]
    assert normalize([0.0, 4.0]) == [0.0, 1.0]
    assert normalize([3.0, 3.0]) == [0.5, 0.5]

    example: list[float] = softmax([2.0, 1.0, 0.0])
    assert abs(example[0] - 0.665241) < 0.000001
    assert abs(example[1] - 0.244728) < 0.000001
    assert abs(example[2] - 0.090031) < 0.000001
    assert softmax([-2.0, -2.0]) == [0.5, 0.5]
    assert softmax([1002.0, 1001.0, 1000.0]) == example

    assert next_token({42: 2.0, 7: 1.0, 99: 0.0}) == 42
    assert next_token({42: -7.0, 7: -2.0, 99: -2.0}) == 7
    assert next_token({99: 4.0, 7: 4.0}) == 99
    assert next_token({99: -10.0}) == 99
