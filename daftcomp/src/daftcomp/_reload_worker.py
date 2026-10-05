"""Private subprocess entry point; replay one captured local save without serving."""

import json
import os
import sys
import traceback
from dataclasses import asdict
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import ModuleType

from pydantic import TypeAdapter

import daftcomp as band

from ._core import Song
from ._reload import WorkerRequest, WorkerResult


class _CapturedSong(BaseException):
    def __init__(self, song: Song) -> None:
        super().__init__()
        self.song = song


def _capture(song: Song, *, port: int, open_browser: bool) -> None:
    """The public run() has already enforced its guard and all validation."""
    raise _CapturedSong(song)


def _error_message(error: BaseException, script: str) -> str:
    location = ""
    if isinstance(error, SyntaxError) and error.lineno is not None:
        location = f" at line {error.lineno}"
    else:
        frames = traceback.extract_tb(error.__traceback__)
        matching = [frame for frame in frames if frame.filename == script]
        if matching:
            location = f" at line {matching[-1].lineno}"
    return f"{type(error).__name__}{location}: {error}"[:1600]


def execute(request: WorkerRequest) -> WorkerResult:
    """Match normal direct-file execution using the exact bytes observed at save."""
    band.clear()
    band.launch = _capture
    os.chdir(request.directory)
    sys.argv = list(request.argv)
    # Fresh interpreters still otherwise reuse timestamp-based student .pyc files.
    sys.pycache_prefix = str(Path(request.source_file).parent / "pycache")
    sys.dont_write_bytecode = True
    script_directory = str(Path(request.script).parent)
    sys.path[:] = [
        script_directory,
        *(path for path in request.import_paths if path != script_directory),
    ]
    main = ModuleType("__main__")
    main.__file__ = request.script
    main.__package__ = None
    main.__loader__ = SourceFileLoader("__main__", request.script)
    main.__spec__ = None
    sys.modules["__main__"] = main
    try:
        source = Path(request.source_file).read_bytes()
        exec(compile(source, request.script, "exec"), main.__dict__)
    except _CapturedSong as captured:
        return WorkerResult(request.digest, captured.song, None)
    except BaseException as error:
        return WorkerResult(request.digest, None, _error_message(error, request.script))
    return WorkerResult(
        request.digest,
        None,
        "The saved score finished without calling run(). Add a run() call, then save again.",
    )


def main() -> None:
    request = TypeAdapter(WorkerRequest).validate_json(Path(sys.argv[1]).read_bytes())
    output = Path(sys.argv[2])
    result = execute(request)
    output.write_text(json.dumps(asdict(result)), encoding="utf-8")


if __name__ == "__main__":
    main()
