"""Export the two EX04 student files as a Gradescope submission."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXERCISE_ROOT = PROJECT_ROOT / "list_utils"
SUBMISSION_FILES = ("utils.py", "utils_test.py")


def export_exercise(output: Path) -> Path:
    """Write only student work, checking both files before creating the ZIP."""
    for filename in SUBMISSION_FILES:
        if not (EXERCISE_ROOT / filename).is_file():
            raise FileNotFoundError(f"Missing list_utils/{filename}.")

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for filename in SUBMISSION_FILES:
            archive.write(EXERCISE_ROOT / filename, arcname=filename)
    return output


def main() -> None:
    """Create a timestamped archive, or use the requested output path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional path for the submission ZIP.")
    args = parser.parse_args()
    output = (
        PROJECT_ROOT / f"{datetime.now():%y.%m.%d-%H.%M.%S}-daftcomp-exercise.zip"
        if args.output is None
        else Path(args.output)
    )
    try:
        archive = export_exercise(output)
    except OSError as error:
        raise SystemExit(f"error: {error}") from error
    print(archive)


if __name__ == "__main__":
    main()
