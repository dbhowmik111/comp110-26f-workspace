# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""Prepare every Python project in this VS Code workspace.

First, we restore the course-managed VS Code workspace file to its committed
version. Then we fetch updates from Git's ``origin``, preview the merge without
changing the student's project files, and apply it only when Git predicts a
conflict-free merge. For each sibling directory that contains a
``pyproject.toml`` file, we then:

1. repair a missing, incomplete, or relocated virtual environment;
2. synchronize the environment to the course's committed, cross-platform
   lockfile;
3. ask uv to check the installed packages for dependency conflicts;
4. parse the project's Python files to catch syntax errors;
5. validate any Jupyter notebooks as JSON; and
6. run recognizable Python tests, when a project has some.

The script uses only Python's standard library. Run the "Sync all workspace
projects" VS Code task, or run ``uv run --managed-python sync.py`` from this
directory.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
import tokenize
from pathlib import Path

# ---------------------------------------------------------------------------
# Part 1: Describe the workspace
# ---------------------------------------------------------------------------
#
# ``support`` sits beside the project directories in the workspace.  Finding
# paths relative to this file makes the program work on Windows, macOS, and
# Linux, no matter where a student stores the workspace.

SUPPORT_DIRECTORY = Path(__file__).resolve().parent
WORKSPACE_DIRECTORY = SUPPORT_DIRECTORY.parent

# These directories contain generated or third-party files.  They are not part
# of a student's source code, so our quick syntax check should ignore them.
IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}

# A quick setup check should never leave a student waiting indefinitely for a
# test suite.  Sixty seconds is generous for the small diagnostic tests this
# script is intended to find.
TEST_TIMEOUT_SECONDS = 60

# Students work in the project directories, but this root-level file is managed
# by the course. Any staged or unstaged changes to it are discarded during sync
# so they cannot prevent course updates from merging cleanly.
MANAGED_WORKSPACE_FILE = "workspace.code-workspace"


# ---------------------------------------------------------------------------
# Part 2: Small helpers for friendly terminal output
# ---------------------------------------------------------------------------


def print_heading(title: str) -> None:
    """Print a title that is easy to find in a busy terminal."""

    line = "=" * 72
    print(f"\n{line}\n{title}\n{line}", flush=True)


def print_result(succeeded: bool, message: str) -> None:
    """Print one consistently formatted result."""

    label = "OK" if succeeded else "FAIL"
    print(f"  [{label}] {message}", flush=True)


def run_command(description: str, command: list[str], directory: Path) -> bool:
    """Run one command, show it to the student, and report whether it worked."""

    print(f"\n  {description}")
    print(f"  > {subprocess.list2cmdline(command)}", flush=True)

    try:
        completed = subprocess.run(command, cwd=directory, check=False)
    except OSError as error:
        print_result(False, f"Could not start the command: {error}")
        return False

    succeeded = completed.returncode == 0
    if succeeded:
        print_result(True, description)
    else:
        print_result(
            False,
            f"{description} (the command exited with code {completed.returncode})",
        )
    return succeeded


def preview_merge(git: str) -> int | None:
    """Return Git's merge preview status without printing its object output."""

    description = "Check whether the course update can be merged without conflicts"
    command = [git, "merge-tree", "--write-tree", "HEAD", "origin/HEAD"]

    print(f"\n  {description}")
    print(f"  > {subprocess.list2cmdline(command)}", flush=True)

    try:
        completed = subprocess.run(
            command,
            cwd=WORKSPACE_DIRECTORY,
            stdout=subprocess.DEVNULL,
            check=False,
        )
    except OSError as error:
        print_result(False, f"Could not start the command: {error}")
        return None

    if completed.returncode == 0:
        print_result(True, description)
    elif completed.returncode == 1:
        print_result(False, f"{description} (Git found merge conflicts)")
    else:
        print_result(
            False,
            f"{description} (Git could not perform the check; the command exited "
            f"with code {completed.returncode})",
        )

    return completed.returncode


# ---------------------------------------------------------------------------
# Part 3: Discover projects instead of hard-coding their names
# ---------------------------------------------------------------------------


def find_projects() -> list[Path]:
    """Return sibling directories that look like uv/Python projects."""

    projects: list[Path] = []

    for possible_project in WORKSPACE_DIRECTORY.iterdir():
        is_project = (
            possible_project.is_dir()
            and possible_project != SUPPORT_DIRECTORY
            and (possible_project / "pyproject.toml").is_file()
        )
        if is_project:
            projects.append(possible_project)

    return sorted(projects, key=lambda path: path.name.casefold())


def find_uv() -> str | None:
    """Return the full path to uv, or ``None`` when uv is not on PATH."""

    return shutil.which("uv")


def find_git() -> str | None:
    """Return the full path to Git, or ``None`` when Git is not on PATH."""

    return shutil.which("git")


def update_workspace(git: str) -> bool:
    """Restore managed settings, then fetch and safely merge origin."""

    print_heading("Updating course workspace")

    restored = run_command(
        "Restore the course-managed VS Code workspace settings",
        [
            git,
            "restore",
            "--source=HEAD",
            "--staged",
            "--worktree",
            "--",
            MANAGED_WORKSPACE_FILE,
        ],
        WORKSPACE_DIRECTORY,
    )
    if not restored:
        print("\n  Project setup will continue so you can see any other problems.")
        return False

    fetched = run_command(
        "Download the latest course history from origin",
        [git, "fetch", "origin"],
        WORKSPACE_DIRECTORY,
    )
    if not fetched:
        print("\n  Project setup will continue so you can see any other problems.")
        return False

    merge_status = preview_merge(git)
    if merge_status == 1:
        print(
            "\n  Git predicts that the course update would conflict with local "
            "work, so it was not applied."
        )
        print("  No student project files were changed.")
        print("  Project setup will continue so you can see any other problems.")
        return False

    if merge_status != 0:
        print(
            "\n  Git could not check the course update safely, so it was not "
            "applied."
        )
        print("  No student project files were changed.")
        print("  Project setup will continue so you can see any other problems.")
        return False

    return run_command(
        "Merge the latest course files",
        [
            git,
            "-c",
            "user.name=COMP110 Workspace Updater",
            "-c",
            "user.email=comp110-workspace-updater@users.noreply.github.com",
            "merge",
            "--no-edit",
            "--no-gpg-sign",
            "origin/HEAD",
        ],
        WORKSPACE_DIRECTORY,
    )


# ---------------------------------------------------------------------------
# Part 4: Heal environments after the workspace has moved
# ---------------------------------------------------------------------------


def environment_is_relocatable(environment: Path) -> bool:
    """Return whether uv marked an environment as safe to move."""

    configuration = environment / "pyvenv.cfg"
    try:
        lines = configuration.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False

    for line in lines:
        key, separator, value = line.partition("=")
        if separator and key.strip().casefold() == "relocatable":
            return value.strip().casefold() == "true"

    return False


def activation_script_for(environment: Path) -> Path | None:
    """Find uv's canonical activation script on POSIX or Windows."""

    candidates = [
        environment / "bin" / "activate",
        environment / "Scripts" / "activate.bat",
    ]
    return next((path for path in candidates if path.is_file()), None)


def environment_path_status(project: Path) -> tuple[bool, str]:
    """Report whether a project's environment still belongs at its current path."""

    environment = project / ".venv"
    if not environment.exists():
        return False, "No virtual environment exists yet."

    activation_script = activation_script_for(environment)
    if not (environment / "pyvenv.cfg").is_file() or activation_script is None:
        return False, "The existing virtual environment is incomplete."

    if environment_is_relocatable(environment):
        return True, "The virtual environment is relocatable."

    try:
        activation_source = activation_script.read_text(
            encoding="utf-8", errors="replace"
        )
    except OSError as error:
        return False, f"Could not inspect the virtual environment: {error}"

    expected_path = str(environment.resolve())
    if activation_script.name.casefold() == "activate.bat":
        path_matches = expected_path.casefold() in activation_source.casefold()
    else:
        path_matches = expected_path in activation_source

    if path_matches:
        return True, "The virtual environment path matches this project."

    message = (
        "The virtual environment contains an old absolute path, usually because "
        "the workspace was moved or renamed."
    )
    return False, message


def ensure_current_environment(uv: str, project: Path) -> bool:
    """Create or automatically replace an environment whose path is stale."""

    path_is_current, message = environment_path_status(project)
    print("\n  Check virtual environment location")

    if path_is_current:
        print_result(True, message)
        return True

    print(f"  [FIX] {message}", flush=True)
    return run_command(
        "Create a relocatable virtual environment at the current project path",
        [
            uv,
            "venv",
            "--clear",
            "--relocatable",
            "--managed-python",
            str(project / ".venv"),
        ],
        project,
    )


# ---------------------------------------------------------------------------
# Part 5: Diagnostics that run inside each project's managed Python
# ---------------------------------------------------------------------------
#
# The main program starts this same file a second time with the project's
# managed interpreter.  This lets ``ast`` understand the exact Python syntax
# that the project uses without adding a second support script.


def project_files_with_suffix(project: Path, suffix: str) -> list[Path]:
    """Find project-owned files with a suffix, skipping generated directories."""

    matching_files: list[Path] = []

    for path in project.rglob(f"*{suffix}"):
        relative_parts = path.relative_to(project).parts
        is_ignored = any(part in IGNORED_DIRECTORY_NAMES for part in relative_parts)

        if path.is_file() and not is_ignored:
            matching_files.append(path)

    return sorted(matching_files)


def check_python_syntax(project: Path) -> bool:
    """Parse Python sources without importing or changing project files."""

    python_files = project_files_with_suffix(project, ".py")
    errors: list[tuple[Path, OSError | SyntaxError | UnicodeError]] = []

    for python_file in python_files:
        try:
            # tokenize.open honors a Python file's encoding declaration.
            with tokenize.open(python_file) as source_file:
                source = source_file.read()
            ast.parse(source, filename=str(python_file))
        except (OSError, SyntaxError, UnicodeError) as error:
            errors.append((python_file, error))

    if not python_files:
        print("  [SKIP] No Python source files found.")
        return True

    if errors:
        for python_file, error in errors:
            relative_path = python_file.relative_to(project)
            print(f"  [FAIL] {relative_path}: {error}")
        return False

    print_result(True, f"Parsed {len(python_files)} Python source file(s).")
    return True


def check_notebooks(project: Path) -> bool:
    """Confirm that each Jupyter notebook contains readable JSON."""

    notebook_files = project_files_with_suffix(project, ".ipynb")
    errors: list[tuple[Path, OSError | UnicodeError | json.JSONDecodeError]] = []

    for notebook_file in notebook_files:
        try:
            with notebook_file.open(encoding="utf-8") as source_file:
                json.load(source_file)
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            errors.append((notebook_file, error))

    if not notebook_files:
        print("  [SKIP] No Jupyter notebooks found.")
        return True

    if errors:
        for notebook_file, error in errors:
            relative_path = notebook_file.relative_to(project)
            print(f"  [FAIL] {relative_path}: {error}")
        return False

    print_result(True, f"Validated {len(notebook_files)} Jupyter notebook(s).")
    return True


def find_test_files(project: Path) -> list[Path]:
    """Find the common ``test_*.py`` and ``*_test.py`` naming patterns."""

    return [
        path
        for path in project_files_with_suffix(project, ".py")
        if path.name.startswith("test_") or path.name.endswith("_test.py")
    ]


def run_quick_tests(project: Path) -> bool:
    """Run a project's tests with pytest when available, otherwise unittest."""

    test_files = find_test_files(project)
    if not test_files:
        print("  [SKIP] No recognizable Python test files found.")
        return True

    if importlib.util.find_spec("pytest") is not None:
        command = [sys.executable, "-m", "pytest", "-q"]
        test_runner = "pytest"
    else:
        command = [sys.executable, "-m", "unittest", "discover", "-q"]
        test_runner = "the standard-library unittest runner"

    print(f"\n  Found {len(test_files)} test file(s); running {test_runner}.")
    print(f"  > {subprocess.list2cmdline(command)}", flush=True)

    try:
        completed = subprocess.run(
            command,
            cwd=project,
            check=False,
            timeout=TEST_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        print_result(
            False,
            f"Tests took longer than {TEST_TIMEOUT_SECONDS} seconds and were stopped.",
        )
        return False
    except OSError as error:
        print_result(False, f"Could not start the tests: {error}")
        return False

    succeeded = completed.returncode == 0
    print_result(
        succeeded, "Quick tests passed." if succeeded else "Quick tests failed."
    )
    return succeeded


def diagnose_project(project: Path) -> int:
    """Run diagnostics inside a project's already-synchronized environment."""

    print(f"  Python {platform.python_version()}")
    print(f"  Interpreter: {sys.executable}")

    checks = [
        check_python_syntax(project),
        check_notebooks(project),
        run_quick_tests(project),
    ]
    return 0 if all(checks) else 1


# ---------------------------------------------------------------------------
# Part 6: Put setup and diagnostics together for one project
# ---------------------------------------------------------------------------


def prepare_project(uv: str, project: Path) -> bool:
    """Synchronize and diagnose one project, returning its overall result."""

    print_heading(f"Preparing project: {project.name}")

    environment_is_ready = ensure_current_environment(uv, project)
    if not environment_is_ready:
        print("  [SKIP] Remaining checks need a usable virtual environment.")
        return False

    synchronized = run_command(
        "Install the package versions selected for this course",
        [uv, "sync", "--locked", "--managed-python"],
        project,
    )

    # Later checks depend on a complete environment.  Avoid a wall of secondary
    # errors when sync has already explained the root problem.
    if not synchronized:
        print("  [SKIP] Remaining checks need a successfully synchronized environment.")
        return False

    dependencies_are_compatible = run_command(
        "Check installed packages for dependency conflicts",
        [uv, "pip", "check", "--python", str(project / ".venv")],
        project,
    )

    diagnostics_passed = run_command(
        "Check source files, notebooks, and quick tests",
        [
            uv,
            "run",
            "--locked",
            "--managed-python",
            "--no-sync",
            "python",
            str(Path(__file__).resolve()),
            "--diagnose-project",
            str(project),
        ],
        project,
    )

    return dependencies_are_compatible and diagnostics_passed


# ---------------------------------------------------------------------------
# Part 7: The student-facing program
# ---------------------------------------------------------------------------


def main() -> int:
    """Prepare every discovered project and print one final summary."""

    print_heading("COMP110 workspace setup")
    print(f"Workspace: {WORKSPACE_DIRECTORY}")
    print("Looking for sibling folders that contain pyproject.toml ...")

    git = find_git()
    if git is None:
        print_result(False, "Git was not found on this computer's PATH.")
        print("  Install Git, restart VS Code, and then run this task again.")
        return 1

    uv = find_uv()
    if uv is None:
        print_result(False, "uv was not found on this computer's PATH.")
        print("  Install uv, restart VS Code, and then run this file again.")
        return 1

    workspace_is_current = update_workspace(git)

    projects = find_projects()
    if not projects:
        print_result(False, "No Python projects were found beside the support folder.")
        return 1

    print_result(True, f"Found {len(projects)} project(s):")
    for project in projects:
        print(f"       - {project.name}")

    results: dict[str, bool] = {}
    try:
        for project in projects:
            results[project.name] = prepare_project(uv, project)
    except KeyboardInterrupt:
        print("\n\nSetup was stopped. It is safe to run this file again.")
        return 130

    print_heading("Workspace setup summary")
    print_result(workspace_is_current, "course workspace files")
    for project_name, succeeded in results.items():
        print_result(succeeded, project_name)

    failed_projects = [name for name, succeeded in results.items() if not succeeded]
    if not workspace_is_current or failed_projects:
        print("\nSome setup steps need attention. Review the [FAIL] message(s) above,")
        print("fix the first reported problem, and then run this file again.")
        return 1

    print("\nEverything is ready. You can start working!")
    return 0


if __name__ == "__main__":
    # ``--diagnose-project`` is an internal mode used by prepare_project().
    # Students can simply run the workspace task without passing any arguments.
    if len(sys.argv) == 3 and sys.argv[1] == "--diagnose-project":
        raise SystemExit(diagnose_project(Path(sys.argv[2]).resolve()))

    raise SystemExit(main())
