"""Internal fresh-process renderer used by the submission packager."""

from __future__ import annotations

from argparse import ArgumentParser
from collections.abc import Sequence
from pathlib import Path

from spacepaint.submission import SubmissionPackagingError, render_completed_artwork


def _parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("script", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--windowed", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = _parser()
    arguments = parser.parse_args(argv)
    try:
        render_completed_artwork(
            arguments.script,
            arguments.output,
            windowed=arguments.windowed,
        )
    except SubmissionPackagingError as error:
        parser.exit(1, f"Spacepaint rendering error: {error}\n")
    except Exception as error:  # noqa: BLE001
        parser.exit(
            1,
            f"Spacepaint rendering error: {type(error).__name__}: {error}\n",
        )


if __name__ == "__main__":
    main()
