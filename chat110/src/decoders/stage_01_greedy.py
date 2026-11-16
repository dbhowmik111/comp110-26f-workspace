"""Stage 1: choose the token whose logit is largest."""

__author__: str = "730986400"


def next_token(logits: dict[int, float]) -> int:
    """Return the first highest-scoring token ID from a nonempty dictionary."""
    token_ids: list[int] = list(logits.keys())
    scores: list[float] = list(logits.values())

    # TODO: Choose the highest-scoring token ID, keeping the first entry on a tie.
    best_index: int = 0
    index: int
    for index in range(1, len(scores)):
        if scores[index] > scores[best_index]:
            best_index = index

    return token_ids[best_index]


if __name__ == "__main__":
    # TODO: Add calls to check your function against the examples in the README.
    assert next_token({42: 2.0, 7: 1.0, 99: 0.0}) == 42
    assert next_token({42: -7.0, 7: -2.0, 99: -2.0}) == 7
    assert next_token({99: 4.0, 7: 4.0}) == 99
    assert next_token({99: -10.0}) == 99
