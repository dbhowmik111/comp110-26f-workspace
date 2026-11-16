"""Stage 1: choose the token whose logit is largest."""

__author__: str = "Your PID goes here."


def next_token(logits: dict[int, float]) -> int:
    """Return the first highest-scoring token ID from a nonempty dictionary."""
    token_ids: list[int] = list(logits.keys())
    scores: list[float] = list(logits.values())

    # TODO: Choose the highest-scoring token ID, keeping the first entry on a tie.
    raise NotImplementedError("Complete next_token for this stage.")


if __name__ == "__main__":
    # TODO: Add calls to check your function against the examples in the README.
    pass
