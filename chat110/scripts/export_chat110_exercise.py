#!/usr/bin/env python3
"""Export all Chat110 stages in one Gradescope ZIP usable for either part."""

import argparse
import json
import zipfile
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
STUDENT_ROOT = SOURCE_ROOT / "decoders"
DEFAULT_ARCHIVE_SUFFIX = "-chat110-exercise.zip"
STAGES = {
    1: "stage_01_greedy",
    2: "stage_02_softmax",
    3: "stage_03_sampling",
    4: "stage_04_top_p",
}


def default_archive_name(now: datetime | None = None) -> str:
    """Match the workspace convention: a timestamped ZIP in the project root."""
    timestamp = datetime.now() if now is None else now
    return f"{timestamp:%y.%m.%d-%H.%M.%S}{DEFAULT_ARCHIVE_SUFFIX}"


def export_exercise(output: Path, student_root: Path = STUDENT_ROOT) -> Path:
    """Include only student Python files and a manifest, never support or models."""
    missing = [f"{name}.py" for name in STAGES.values() if not (student_root / f"{name}.py").is_file()]
    if missing:
        raise ValueError("Missing required decoder files: " + ", ".join(missing))
    sources = sorted(source for source in student_root.rglob("*.py") if source.is_file())
    for source in sources:
        if source.is_symlink() or not source.resolve().is_relative_to(student_root.resolve()):
            raise ValueError(f"Student files must not be symbolic links: {source}")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sources:
            if "__pycache__" not in source.parts:
                archive.write(source, Path("decoders") / source.relative_to(student_root))
        archive.writestr("decoding-submission.json", json.dumps({
            "schema_version": 1,
            "exercise": "chat110",
            "stages": {str(stage): f"decoders.{name}" for stage, name in STAGES.items()},
        }, indent=2) + "\n")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path,
        help="Archive path (default: yy.mm.dd-hh.mm.ss-chat110-exercise.zip in the project root)",
    )
    args = parser.parse_args()
    try:
        output = args.output if args.output is not None else PROJECT_ROOT / default_archive_name()
        print(export_exercise(output))
    except (OSError, ValueError) as error:
        parser.exit(1, f"Export failed: {error}\n")


if __name__ == "__main__":
    main()
