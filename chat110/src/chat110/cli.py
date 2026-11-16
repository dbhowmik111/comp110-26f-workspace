"""Chat with Gemma using a selected COMP110 next_token implementation."""

import argparse
import random
import sys
from collections.abc import Callable
from importlib import import_module
from math import isfinite

from .model import BundleError
from .runtime import GemmaChat

STAGES = {
    1: "decoders.stage_01_greedy",
    2: "decoders.stage_02_softmax",
    3: "decoders.stage_03_sampling",
    4: "decoders.stage_04_top_p",
}


def select_next_token(
    stage: int, top_p: float,
) -> Callable[[dict[int, float]], int]:
    """Instructor wiring: choose a student implementation and apply settings."""
    module = import_module(STAGES[stage])
    if stage == 4:
        module.TOP_P = top_p
    return module.next_token


def stream_reply(
    chat: GemmaChat, prompt: str, next_token: Callable[[dict[int, float]], int],
    max_tokens: int, *, prefix: str = "",
) -> None:
    """Print each decoded chunk immediately and finish the line even on failure."""
    def write_text(text: str) -> None:
        print(text, end="", flush=True)

    if prefix:
        write_text(prefix)
    try:
        chat.reply(prompt, next_token, max_tokens=max_tokens, on_text=write_text)
    finally:
        print()


def run_interactive(
    chat: GemmaChat, next_token: Callable[[dict[int, float]], int], max_tokens: int,
) -> None:
    """Read prompts until the user exits, preserving successful conversation turns."""
    print("Gemma 3 270M IT by Google DeepMind")
    print("Type /quit to exit or /reset to start a new conversation.\n")
    while True:
        try:
            prompt = input("You: ")
        except EOFError:
            print()
            return
        if prompt.strip() == "/quit":
            return
        if prompt.strip() == "/reset":
            chat.reset()
            print("Started a new conversation.\n")
            continue
        if not prompt.strip():
            continue
        try:
            stream_reply(chat, prompt, next_token, max_tokens, prefix="Gemma: ")
        except ValueError as error:
            print(f"Could not generate a reply: {error}", file=sys.stderr)
            continue
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", nargs="?", help="Give one reply; omit for interactive chat")
    parser.add_argument(
        "--stage", type=int, choices=STAGES, default=1,
        help="Student stage to use (default: 1, greedy)",
    )
    parser.add_argument("--top-p", type=float, help="Top-p threshold for stage 4 (0 < p <= 1; default: 0.9)")
    parser.add_argument("--seed", type=int, help="Seed randomness once for repeatable experiments")
    parser.add_argument("--max-tokens", type=int, default=128, help="Maximum tokens per reply (default: 128)")
    args = parser.parse_args()
    if args.prompt is not None and not args.prompt.strip():
        parser.error("The prompt must be nonempty.")
    if args.max_tokens <= 0:
        parser.error("--max-tokens must be positive.")
    if args.top_p is not None and args.stage < 4:
        parser.error("--top-p applies to stage 4.")
    top_p = args.top_p if args.top_p is not None else 0.9
    if not isfinite(top_p) or not 0.0 < top_p <= 1.0:
        parser.error("--top-p must satisfy 0 < p <= 1.")

    next_token = select_next_token(args.stage, top_p)
    try:
        chat = GemmaChat()
        if args.seed is not None:
            random.seed(args.seed)
        if args.prompt is not None:
            stream_reply(chat, args.prompt, next_token, args.max_tokens)
        else:
            run_interactive(chat, next_token, args.max_tokens)
    except (BundleError, ValueError, NotImplementedError) as error:
        parser.exit(1, f"Chat failed: {error}\n")
    except KeyboardInterrupt:
        print(file=sys.stderr)


if __name__ == "__main__":
    main()
