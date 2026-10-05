"""Watch one local entry script and publish only completed, validated reruns."""

import asyncio
import hashlib
import json
import os
import subprocess
import sys
from contextlib import suppress
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock

from pydantic import TypeAdapter

from ._core import Song

POLL_INTERVAL: float = 0.2
DEBOUNCE_SECONDS: float = 0.25
WORKER_TIMEOUT: float = 10.0
MAX_RESULT_BYTES: int = 2 * 1024 * 1024


@dataclass(frozen=True)
class Source:
    contents: bytes
    digest: str

    @classmethod
    def read(cls, path: Path) -> "Source":
        contents = path.read_bytes()
        return cls(contents, hashlib.sha256(contents).hexdigest())


@dataclass(frozen=True)
class EntryScript:
    path: Path
    argv: tuple[str, ...]
    directory: Path
    import_paths: tuple[str, ...]
    initial_digest: str


def discover_script() -> EntryScript | None:
    """Enable reruns for a real student .py entry point, never the package demo."""
    if os.environ.get("DAFTCOMP_LIVE_RELOAD") == "0":
        return None
    filename: object = getattr(sys.modules.get("__main__"), "__file__", None)
    if not isinstance(filename, str):
        return None
    try:
        path = Path(filename).resolve()
        if path.suffix.lower() != ".py" or path == Path(__file__).with_name("__main__.py"):
            return None
        source = Source.read(path)
        return EntryScript(path, tuple(sys.argv), Path.cwd(), tuple(sys.path), source.digest)
    except OSError:
        return None


@dataclass(frozen=True)
class SessionState:
    song: Song
    launch_id: str
    revision: int
    reload_enabled: bool
    reload_error: str | None
    score_filename: str | None
    reloading: bool


class Session:
    """Replace one immutable state under a lock shared with HTTP reader threads."""

    def __init__(self, song: Song, entry: EntryScript | None = None) -> None:
        self._lock = Lock()
        self._state = SessionState(
            song,
            song.session_id,
            0,
            entry is not None,
            None,
            entry.path.name if entry else None,
            False,
        )

    def snapshot(self) -> SessionState:
        with self._lock:
            return self._state

    def begin_reload(self) -> None:
        with self._lock:
            self._state = replace(self._state, reloading=True, reload_error=None)

    def cancel_reload(self) -> None:
        with self._lock:
            self._state = replace(self._state, reloading=False)

    def publish(self, song: Song) -> None:
        with self._lock:
            self._state = replace(
                self._state,
                song=song,
                revision=self._state.revision + 1,
                reload_error=None,
                reloading=False,
            )

    def fail(self, message: str) -> None:
        with self._lock:
            self._state = replace(self._state, reload_error=message, reloading=False)


@dataclass(frozen=True)
class WorkerRequest:
    script: str
    argv: tuple[str, ...]
    directory: str
    import_paths: tuple[str, ...]
    source_file: str
    digest: str


@dataclass(frozen=True)
class WorkerResult:
    digest: str
    song: Song | None
    error: str | None


async def _stop_worker(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    with suppress(ProcessLookupError):
        process.terminate()
    try:
        await asyncio.wait_for(process.wait(), timeout=1)
    except TimeoutError:
        with suppress(ProcessLookupError):
            process.kill()
        await process.wait()


async def evaluate(entry: EntryScript, source: Source) -> WorkerResult:
    """Execute a captured save once; cancellation always terminates and reaps it."""
    process: asyncio.subprocess.Process | None = None
    with TemporaryDirectory(prefix="daftcomp-reload-") as directory:
        temporary = Path(directory)
        source_path = temporary / "saved-source.py"
        request_path = temporary / "request.json"
        result_path = temporary / "result.json"
        source_path.write_bytes(source.contents)
        request = WorkerRequest(
            str(entry.path),
            entry.argv,
            str(entry.directory),
            entry.import_paths,
            str(source_path),
            source.digest,
        )
        request_path.write_text(json.dumps(asdict(request)), encoding="utf-8")
        environment = os.environ.copy()
        environment["DAFTCOMP_LIVE_RELOAD"] = "0"
        environment["DAFTCOMP_RELOAD_WORKER"] = "1"
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "daftcomp._reload_worker",
                str(request_path),
                str(result_path),
                cwd=entry.directory,
                env=environment,
                stdin=subprocess.DEVNULL,
                start_new_session=sys.platform != "win32",
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            )
            try:
                returncode = await asyncio.wait_for(process.wait(), timeout=WORKER_TIMEOUT)
            except TimeoutError:
                return WorkerResult(
                    source.digest,
                    None,
                    f"The saved score did not reach run() within {WORKER_TIMEOUT:g} seconds. "
                    "Check for an endless loop or blocking operation, then save again.",
                )
            if returncode != 0:
                return WorkerResult(
                    source.digest,
                    None,
                    f"The saved score's Python process exited with code {returncode}. Save again.",
                )
            if result_path.stat().st_size > MAX_RESULT_BYTES:
                raise ValueError("The saved score produced an oversized result.")
            result = TypeAdapter(WorkerResult).validate_json(result_path.read_bytes())
            if result.digest != source.digest or (result.song is None) == (result.error is None):
                raise ValueError("The saved score did not produce a complete snapshot.")
            return result
        except (OSError, ValueError) as error:
            return WorkerResult(source.digest, None, f"Could not reload the saved score: {error}")
        finally:
            if process is not None:
                cleanup = asyncio.create_task(_stop_worker(process))
                try:
                    await asyncio.shield(cleanup)
                except asyncio.CancelledError:
                    await cleanup
                    raise


async def watch(entry: EntryScript, session: Session) -> None:
    """Debounce saves and keep at most one fresh interpreter running at a time."""
    loop = asyncio.get_running_loop()
    observed = entry.initial_digest
    attempted = entry.initial_digest
    stable_since = loop.time()
    active: asyncio.Task[WorkerResult] | None = None
    active_digest: str | None = None
    try:
        while True:
            source: Source | None = None
            read_error: str | None = None
            try:
                source = Source.read(entry.path)
                key = source.digest
            except OSError as error:
                read_error = (
                    f"Cannot read {entry.path.name}: {error.strerror}. Save the file again."
                )
                key = f"unreadable:{read_error}"
            if key != observed:
                observed = key
                stable_since = loop.time()
            if active is not None and key != active_digest:
                active.cancel()
                await asyncio.gather(active, return_exceptions=True)
                active = None
                session.cancel_reload()
            if active is not None and active.done():
                try:
                    result = await active
                except Exception as error:
                    # Temporary-directory or interpreter startup failures must not
                    # disable future saves or replace the last valid composition.
                    result = WorkerResult(key, None, f"Could not reload the saved score: {error}")
                active = None
                attempted = key
                if result.song is not None:
                    session.publish(result.song)
                    print(
                        f"Updated {result.song.title}. Click Play to hear the saved score.",
                        flush=True,
                    )
                else:
                    message = result.error or "The saved score could not be compiled."
                    session.fail(message)
                    print(f"Reload error: {message}", flush=True)
            if (
                active is None
                and key != attempted
                and loop.time() - stable_since >= DEBOUNCE_SECONDS
            ):
                if source is None:
                    session.fail(read_error or "The score file is unavailable. Save it again.")
                    attempted = key
                else:
                    session.begin_reload()
                    active_digest = source.digest
                    active = asyncio.create_task(evaluate(entry, source))
            await asyncio.sleep(POLL_INTERVAL)
    finally:
        if active is not None:
            active.cancel()
            await asyncio.gather(active, return_exceptions=True)
        session.cancel_reload()
