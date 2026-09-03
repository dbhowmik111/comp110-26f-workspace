"""Create a Gradescope submission with programs and rendered artwork."""

from __future__ import annotations

import subprocess
import sys
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from os import PathLike
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any, cast
from zipfile import ZIP_DEFLATED, ZipFile

from spacepaint.main import GameConfig, StudentProgramProblem, create_scene_app

STUDENT_CODE_NAME = "student_code.py"
DEFAULT_SCRIPTS = (Path(STUDENT_CODE_NAME),)
DEFAULT_ARCHIVE_SUFFIX = "-spacepaint.zip"
CAPTURE_FRAME_COUNT = 8
CAPTURE_SCALE = 4
CAPTURE_SIZE = (1280 * CAPTURE_SCALE, 720 * CAPTURE_SCALE)


class SubmissionPackagingError(RuntimeError):
    """A student-facing failure to create a valid submission archive."""


@dataclass(frozen=True, slots=True)
class SubmissionProgram:
    """One submitted script and the screenshot rendered from it."""

    script: Path
    artwork: Path
    archive_directory: Path = Path()


def artwork_name_for_script(script: Path) -> str:
    """Return the PNG filename paired with a submitted Python script."""
    return f"{script.stem}.png"


def _archive_path_for_script(script: Path) -> Path:
    """Preserve a script's path relative to the current project directory."""
    try:
        return script.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        return Path(script.name)


def default_archive_name(now: datetime | None = None) -> str:
    """Return the timestamped default filename for a student submission."""
    timestamp = datetime.now() if now is None else now
    return f"{timestamp:%y.%m.%d-%H.%M.%S}{DEFAULT_ARCHIVE_SUFFIX}"


def _problem_message(problem: StudentProgramProblem) -> str:
    return f"student program failed at {problem.location}: {problem.summary}"


def _panda_filename(path: Path) -> PathLike[str]:
    """Convert an OS-native path to Panda3D's portable filename representation."""
    panda = cast(Any, import_module("panda3d.core"))
    return cast(PathLike[str], panda.Filename.from_os_specific(str(path.resolve())))


def _load_submission_module(script: Path) -> ModuleType:
    """Load one explicit script while making its sibling modules importable."""
    module_name = "_spacepaint_submission_program"
    spec = spec_from_file_location(module_name, script)
    if spec is None or spec.loader is None:
        raise SubmissionPackagingError(f"could not load student program from {script}")

    module = module_from_spec(spec)
    previous_module = sys.modules.get(module_name)
    script_directory = str(script.parent.resolve())
    sys.modules[module_name] = module
    sys.path.insert(0, script_directory)
    try:
        spec.loader.exec_module(module)
    except Exception as error:
        raise SubmissionPackagingError(
            f"student program failed while loading {script.name}: "
            f"{type(error).__name__}: {error}"
        ) from error
    finally:
        sys.path.remove(script_directory)
        if previous_module is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous_module
    return module


def render_completed_artwork(
    script: Path,
    output: Path,
    *,
    size: tuple[int, int] = CAPTURE_SIZE,
    windowed: bool = False,
) -> Path:
    """Render one explicit script from the completed default artwork camera."""
    if not script.is_file():
        raise SubmissionPackagingError(f"could not find {script}")
    output.parent.mkdir(parents=True, exist_ok=True)
    student_module = _load_submission_module(script.resolve())
    config = GameConfig(
        title=f"Spacepaint Submission Preview — {script.name}",
        size=size,
        vsync=False,
        show_hud=False,
    )
    app, scene = create_scene_app(
        config,
        window_type=None if windowed else "offscreen",
        student_module=student_module,
    )
    try:
        if scene.problem is not None:
            raise SubmissionPackagingError(_problem_message(scene.problem))
        scene.show_completed_artwork()
        for _ in range(CAPTURE_FRAME_COUNT):
            app.step()
        screenshot_result = app.screenshot(
            namePrefix=_panda_filename(output),
            defaultFilename=False,
        )
        if screenshot_result is None:
            raise SubmissionPackagingError(
                f"the renderer did not write {output.name}"
            )
        screenshot = Path(screenshot_result)
        if not screenshot.is_file() or screenshot.stat().st_size == 0:
            raise SubmissionPackagingError(
                f"the rendered {output.name} is missing or empty"
            )
        return screenshot
    finally:
        app.destroy()


def _render_artwork_in_fresh_process(
    script: Path,
    output: Path,
    *,
    windowed: bool,
) -> Path:
    """Render one program in an isolated graphics process."""
    command = [
        sys.executable,
        "-m",
        "spacepaint._submission_renderer",
        str(script),
        str(output),
    ]
    if windowed:
        command.append("--windowed")
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip()
        if not details:
            details = f"renderer exited with status {completed.returncode}"
        raise SubmissionPackagingError(
            f"could not render {script.name}: {details[-4000:]}"
        )
    if not output.is_file() or output.stat().st_size == 0:
        raise SubmissionPackagingError(
            f"the renderer did not produce {output.name} for {script.name}"
        )
    return output


def _validated_scripts(
    scripts: Sequence[Path],
    output: Path,
) -> tuple[tuple[Path, Path], ...]:
    if not scripts:
        raise SubmissionPackagingError("select at least one Python script")

    validated: list[tuple[Path, Path]] = []
    archive_names: set[str] = set()
    output_path = output.resolve()
    for configured_script in scripts:
        if configured_script.suffix != ".py":
            raise SubmissionPackagingError(
                f"submission script must end in .py: {configured_script}"
            )
        script = configured_script.resolve()
        if not script.is_file():
            raise SubmissionPackagingError(
                f"could not find {configured_script}; run this command from the "
                "Spacepaint project folder"
            )
        if script == output_path:
            raise SubmissionPackagingError(
                f"output archive would overwrite submission script: {configured_script}"
            )
        archive_path = _archive_path_for_script(script)
        archive_name = archive_path.as_posix()
        if archive_name in archive_names:
            raise SubmissionPackagingError(
                f"submission scripts must have unique archive paths: {archive_name}"
            )
        archive_names.add(archive_name)
        validated.append((script, archive_path))
    return tuple(validated)


def create_submission_archive(
    programs: Sequence[SubmissionProgram],
    output: Path,
) -> Path:
    """Write an atomic ZIP containing every script and PNG pair."""
    if not programs:
        raise SubmissionPackagingError("select at least one program to archive")
    if output.exists() and output.is_dir():
        raise SubmissionPackagingError(f"output path is a directory: {output}")

    archive_names: set[str] = set()
    for program in programs:
        for source in (program.script, program.artwork):
            if not source.is_file():
                raise SubmissionPackagingError(f"could not find {source}")
            archive_path = program.archive_directory / source.name
            if archive_path.is_absolute() or ".." in archive_path.parts:
                raise SubmissionPackagingError(
                    f"submission archive path must be relative: {archive_path}"
                )
            archive_name = archive_path.as_posix()
            if archive_name in archive_names:
                raise SubmissionPackagingError(
                    f"submission files must have unique archive paths: {archive_name}"
                )
            archive_names.add(archive_name)

    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(
        prefix=".spacepaint-archive-", dir=output.parent
    ) as temporary:
        temporary_archive = Path(temporary) / output.name
        with ZipFile(temporary_archive, "w", compression=ZIP_DEFLATED) as archive:
            for program in programs:
                archive.write(
                    program.script,
                    arcname=(program.archive_directory / program.script.name).as_posix(),
                )
                archive.write(
                    program.artwork,
                    arcname=(program.archive_directory / program.artwork.name).as_posix(),
                )
        temporary_archive.replace(output)
    return output.resolve()


def package_submission(
    output: Path | None = None,
    *,
    scripts: Sequence[Path] = DEFAULT_SCRIPTS,
    windowed: bool = False,
) -> Path:
    """Render and package an explicit collection of student programs."""
    resolved_output = Path(default_archive_name()) if output is None else output
    validated_scripts = _validated_scripts(scripts, resolved_output)
    with TemporaryDirectory(prefix="spacepaint-submission-") as temporary:
        temporary_directory = Path(temporary)
        programs: list[SubmissionProgram] = []
        for script, archive_path in validated_scripts:
            artwork = _render_artwork_in_fresh_process(
                script,
                temporary_directory / archive_path.with_suffix(".png"),
                windowed=windowed,
            )
            programs.append(
                SubmissionProgram(script, artwork, archive_path.parent)
            )
        return create_submission_archive(programs, resolved_output)


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description=(
            "Render one PNG per Spacepaint program and create a Gradescope-ready "
            "submission ZIP."
        )
    )
    parser.add_argument(
        "--scripts",
        type=Path,
        nargs="+",
        action="append",
        metavar="SCRIPT",
        help=(
            "Python scripts to render and submit; may be repeated "
            f"(default: {STUDENT_CODE_NAME})"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "archive path (default: current local time formatted as "
            "yy.mm.dd-hh.mm.ss-spacepaint.zip)"
        ),
    )
    parser.add_argument(
        "--windowed",
        action="store_true",
        help="show a normal graphics window instead of rendering offscreen",
    )
    return parser


def _configured_scripts(arguments: Namespace) -> tuple[Path, ...]:
    groups = arguments.scripts
    if groups is None:
        return DEFAULT_SCRIPTS
    return tuple(script for group in groups for script in group)


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    windowed = cast(bool, arguments.windowed)
    scripts = _configured_scripts(arguments)
    try:
        archive = package_submission(
            cast(Path | None, arguments.output),
            scripts=scripts,
            windowed=windowed,
        )
    except SubmissionPackagingError as error:
        parser.exit(1, f"Spacepaint submission error: {error}\n")
    # Translate renderer- and platform-specific failures into a concise CLI error.
    except Exception as error:  # noqa: BLE001
        fallback = " Try again with --windowed." if not windowed else ""
        parser.exit(
            1,
            f"Spacepaint submission error: artwork rendering failed: {error}.{fallback}\n",
        )
    archive_paths = tuple(
        archive_path.as_posix()
        for script in scripts
        for archive_path in (
            _archive_path_for_script(script),
            _archive_path_for_script(script).with_suffix(".png"),
        )
    )
    print(f"Created {archive}")
    print(f"Archive contents: {', '.join(archive_paths)}")


if __name__ == "__main__":
    main()
