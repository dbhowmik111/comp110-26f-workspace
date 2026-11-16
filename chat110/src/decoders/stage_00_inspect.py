"""Warm-up: inspect real Gemma tokens and their next-token scores."""

from chat110.support import next_token_logits, token_text, tokenize


def main() -> None:
    """Tokenize a prompt, then inspect its ten highest-scoring continuations."""
    prompt: str = "The cat sat on the"
    token_ids: list[int] = tokenize(prompt)

    print("Prompt:", repr(prompt))
    print("\nPrompt tokens")
    print(f"{'Position':>8}  {'Token ID':>8}  Text")
    print(f"{'-' * 8}  {'-' * 8}  {'-' * 16}")
    for index in range(len(token_ids)):
        print(f"{index:>8}  {token_ids[index]:>8}  {token_text(token_ids[index])!r}")

    logits: dict[int, float] = next_token_logits(prompt, top_k=10)
    print(f"\nTop {len(logits)} next-token candidates (highest score first)")
    inspect_logits(logits)
    print("\nText is quoted to show spaces. Logits are scores, not probabilities.")


def inspect_logits(logits: dict[int, float]) -> None:
    """Display token IDs alongside their scores, in dictionary insertion order."""
    token_ids: list[int] = list(logits.keys())
    scores: list[float] = list(logits.values())

    print(f"{'Position':>8}  {'Token ID':>8}  {'Text':<20}  {'Logit':>8}")
    print(f"{'-' * 8}  {'-' * 8}  {'-' * 20}  {'-' * 8}")
    for index in range(len(token_ids)):
        # Field widths align the columns; .3f rounds only the displayed score.
        print(f"{index:>8}  {token_ids[index]:>8}  {token_text(token_ids[index])!r:<20}  {scores[index]:>8.3f}")


if __name__ == "__main__":
    main()
