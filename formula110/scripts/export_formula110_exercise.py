#!/usr/bin/env python3
"""Export the four Formula 110 exercise levels as a Gradescope submission."""

from __future__ import annotations

import argparse
import json
import zipfile
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
CONTROLLERS_ROOT = SOURCE_ROOT / "controllers"
DEFAULT_ARCHIVE_SUFFIX = "-formula110-exercise.zip"
SUBMISSION_MANIFEST_NAME = "formula110-exercise-submission.json"
LEVEL_MODULES = {
    "0": "controllers.level_0",
    "1": "controllers.level_1",
    "2": "controllers.level_2",
    "3": "controllers.level_3",
}


def default_archive_name(now: datetime | None = None) -> str:
    """Return the timestamped default filename for an exercise submission."""
    timestamp = datetime.now() if now is None else now
    return f"{timestamp:%y.%m.%d-%H.%M.%S}{DEFAULT_ARCHIVE_SUFFIX}"


def module_source(module_name: str) -> Path:
    """Resolve one dotted controller module to its source file."""
    return SOURCE_ROOT.joinpath(*module_name.split(".")).with_suffix(".py")


def exercise_sources() -> tuple[Path, ...]:
    """Return the controller package's Python files that are present."""
    return tuple(
        sorted(
            path
            for path in CONTROLLERS_ROOT.rglob("*.py")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
        )
    )


def export_exercise(output: Path) -> Path:
    """Write the four levels and local Python helpers to a submission ZIP."""
    sources = exercise_sources()
    resolved_output = output.resolve()
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(resolved_output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sources:
            archive.write(source, arcname=source.relative_to(SOURCE_ROOT))
        archive.writestr(
            SUBMISSION_MANIFEST_NAME,
            json.dumps(
                {
                    "schema_version": 1,
                    "exercise": "formula110-progression",
                    "levels": LEVEL_MODULES,
                },
                indent=2,
            )
            + "\n",
        )
    return resolved_output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "archive path (default: Formula110 project root with current local "
            "time formatted as yy.mm.dd-hh.mm.ss-formula110-exercise.zip)"
        ),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_path = PROJECT_ROOT / default_archive_name() if args.output is None else args.output
    try:
        output = export_exercise(output_path)
    except FileNotFoundError as error:
        raise SystemExit(f"error: {error}") from error
    print(output)


if __name__ == "__main__":
    main()
