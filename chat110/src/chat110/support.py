"""Instructor-provided helpers for inspecting Gemma and ranking candidates."""

from __future__ import annotations

import os
from functools import cache
from typing import TYPE_CHECKING

from .model import ensure_model

if TYPE_CHECKING:
    from transformers import PreTrainedModel, PreTrainedTokenizerBase


def tokenize(text: str) -> list[int]:
    """Return the text's token IDs without adding beginning or chat markers."""
    return _get_tokenizer().encode(text, add_special_tokens=False)


def token_text(token_id: int) -> str:
    """Decode one token ID, preserving spaces and special markers."""
    tokenizer = _get_tokenizer()
    if type(token_id) is not int or not 0 <= token_id < tokenizer.vocab_size:
        raise ValueError("token_id must be an ID in Gemma's vocabulary.")
    return tokenizer.decode(
        [token_id], skip_special_tokens=False, clean_up_tokenization_spaces=False,
    )


def next_token_logits(prompt: str, top_k: int = 10) -> dict[int, float]:
    """Return up to top_k raw continuation scores, highest first, without chat formatting."""
    if not prompt.strip():
        raise ValueError("Enter some text for Gemma to continue.")
    if type(top_k) is not int or top_k < 1:
        raise ValueError("top_k must be a positive integer.")

    import torch

    tokenizer = _get_tokenizer()
    model = _get_model()
    # Include <bos>, matching the direct-completion example in the README.
    inputs = tokenizer(prompt, add_special_tokens=True, return_tensors="pt")
    if inputs["input_ids"].shape[1] >= model.config.max_position_embeddings:
        raise ValueError("The prompt is too long to predict another token. Use less text.")
    with torch.inference_mode():
        scores: list[float] = model(**inputs, logits_to_keep=1).logits[0, -1].tolist()
    return {token_id: scores[token_id] for token_id in rank_indices(scores)[:top_k]}


def rank_indices(probabilities: list[float]) -> list[int]:
    """Given: largest probability first; ties retain the original list order."""
    # Sorting and the key function are instructor implementation details.
    return sorted(
        range(len(probabilities)),
        key=lambda index: probabilities[index],
        reverse=True,
    )


@cache
def _get_tokenizer() -> PreTrainedTokenizerBase:
    """Load the bundled tokenizer once, when a caller first needs it."""
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(
        str(ensure_model()), local_files_only=True, trust_remote_code=False,
    )


@cache
def _get_model() -> PreTrainedModel:
    """Load the model once, using the same settings for inspection and chat."""
    import torch
    from transformers import AutoModelForCausalLM
    from transformers.utils import logging

    logging.disable_progress_bar()
    torch.set_num_threads(min(4, os.cpu_count() or 1))
    return AutoModelForCausalLM.from_pretrained(
        str(ensure_model()), dtype=torch.float32, use_safetensors=True,
        attn_implementation="sdpa", local_files_only=True, trust_remote_code=False,
    ).cpu().eval()
