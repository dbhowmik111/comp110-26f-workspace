"""Instructor-provided Gemma runtime for the student's next_token function."""

from collections.abc import Callable

from .support import _get_model, _get_tokenizer


class GemmaChat:
    """Load Gemma once, keep conversation history, and delegate token selection."""

    def __init__(self) -> None:
        import torch

        self.torch = torch
        self.tokenizer = _get_tokenizer()
        self.model = _get_model()
        stops = self.model.generation_config.eos_token_id
        self.stop_ids = set(stops if isinstance(stops, list) else [stops])
        self.history: list[dict[str, str]] = []

    def reset(self) -> None:
        """Start a new conversation while keeping the loaded model."""
        self.history.clear()

    def reply(
        self, prompt: str, next_token: Callable[[dict[int, float]], int],
        *, max_tokens: int = 128, on_text: Callable[[str], None] | None = None,
    ) -> str:
        """Generate a reply, optionally sending decoded text to on_text as it arrives."""
        if not prompt.strip():
            raise ValueError("Enter a nonempty prompt.")
        if max_tokens <= 0:
            raise ValueError("The reply token limit must be positive.")

        messages = [*self.history, {"role": "user", "content": prompt}]
        input_ids = self.tokenizer.apply_chat_template(
            messages, tokenize=True, return_dict=False, return_tensors="pt",
            add_generation_prompt=True,
        )
        remaining = self.model.config.max_position_embeddings - input_ids.shape[1]
        if remaining <= 0:
            raise ValueError(
                "The prompt and conversation exceed the model's context window. "
                "Use /reset and try a shorter prompt."
            )

        generated: list[int] = []
        emitted_length = 0
        cache = None
        with self.torch.inference_mode():
            for _ in range(min(max_tokens, remaining)):
                output = self.model(
                    input_ids=input_ids, past_key_values=cache,
                    use_cache=True, logits_to_keep=1,
                )
                # This is the complete vocabulary, in vocabulary-ID order.
                scores: list[float] = output.logits[0, -1].tolist()
                logits: dict[int, float] = {}
                for token_id in range(len(scores)):
                    logits[token_id] = scores[token_id]

                # The student's code makes the actual next-token decision.
                token_id = next_token(logits)
                if type(token_id) is not int or not 0 <= token_id < len(scores):
                    raise ValueError(
                        "next_token must return an integer token ID from the "
                        "logits dictionary, rather than a score."
                    )
                if token_id in self.stop_ids:
                    break

                generated.append(token_id)
                input_ids = input_ids.new_tensor([[token_id]])
                cache = output.past_key_values
                if on_text is not None:
                    # Decode in context: a character can span several byte tokens.
                    text = self.tokenizer.decode(
                        generated, skip_special_tokens=True,
                        clean_up_tokenization_spaces=False,
                    )
                    # Hold incomplete UTF-8 at the end until more tokens arrive.
                    text = text.rstrip("\ufffd")
                    chunk = text[emitted_length:]
                    if chunk:
                        on_text(chunk)
                        emitted_length = len(text)

        reply = self.tokenizer.decode(
            generated, skip_special_tokens=True, clean_up_tokenization_spaces=False,
        )
        if on_text is not None and emitted_length < len(reply):
            on_text(reply[emitted_length:])
        # Commit the turn only after generation completes successfully.
        self.history.extend([
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": reply},
        ])
        return reply
