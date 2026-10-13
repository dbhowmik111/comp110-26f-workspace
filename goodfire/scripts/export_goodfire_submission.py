"""Export your Good Fire files as a Gradescope submission ZIP."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PART1_FILES = (
    "goodfire/cover.py",
    "goodfire/sketch.py",
    "goodfire/landscape.py",
)
PART2_FILES = PART1_FILES + (
    "goodfire/weather.py",
    "goodfire/tactics.py",
    "goodfire/recursion.py",
    "goodfire/simulation.py",
    "goodfire/plan.py",
)
SUBMISSION_FILES = {"1": PART1_FILES, "2": PART2_FILES}


def export_submission(part: str, output: Path) -> Path:
    """Write only student files, checking they all exist first."""
    files = SUBMISSION_FILES[part]
    for relative in files:
        if not (PROJECT_ROOT / relative).is_file():
            raise FileNotFoundError(f"Missing {relative}.")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for relative in files:
            archive.write(PROJECT_ROOT / relative, arcname=relative)
    return output


def main() -> None:
    """Create a timestamped archive, or use the requested output path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--part", choices=sorted(SUBMISSION_FILES), required=True
    )
    parser.add_argument(
        "--output", type=Path, help="Optional path for the ZIP."
    )
    args = parser.parse_args()
    stamp = f"{datetime.now():%y.%m.%d-%H.%M.%S}"
    output = (
        PROJECT_ROOT / f"{stamp}-goodfire-part{args.part}.zip"
        if args.output is None
        else Path(args.output)
    )
    try:
        archive = export_submission(args.part, output)
    except OSError as error:
        raise SystemExit(f"error: {error}") from error
    print(f"Upload this file to Gradescope:\n{archive}")


if __name__ == "__main__":
    main()
