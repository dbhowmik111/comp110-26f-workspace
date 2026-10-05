"""Serve only bundled resources, a single validated snapshot, and the studio page."""

import asyncio
import signal
import socket
import sys
import webbrowser
from collections.abc import Callable, Generator
from contextlib import contextmanager, suppress
from importlib.resources import files

import uvicorn
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ._core import Song
from ._reload import Session, discover_script, watch

STARTUP_TIMEOUT: float = 5.0


class PlayerServer(uvicorn.Server):
    """Return to the caller after interruption on both Windows and Unix."""

    @contextmanager
    def capture_signals(self) -> Generator[None, None, None]:
        signals = [signal.SIGINT, signal.SIGTERM]
        if sys.platform == "win32":
            signals.append(signal.SIGBREAK)
        original = {sig: signal.signal(sig, self.handle_exit) for sig in signals}
        try:
            yield
        finally:
            for sig, handler in original.items():
                signal.signal(sig, handler)


def _page(name: str) -> HTMLResponse:
    html = files("daftcomp").joinpath(f"static/{name}").read_text(encoding="utf-8")
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


def _base_app() -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.mount("/static", StaticFiles(packages=[("daftcomp", "static")]), name="static")

    @app.get("/studio", response_class=HTMLResponse)
    def studio_page() -> HTMLResponse:
        return _page("studio.html")

    return app


def create_studio_app() -> FastAPI:
    """Serve the keyboard studio alone; it needs no score or Python lists."""
    app = _base_app()

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        return _page("studio.html")

    return app


def create_app(song: Song, *, session: Session | None = None) -> FastAPI:
    app = _base_app()
    current = session if session is not None else Session(song)

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        return _page("index.html")

    @app.get("/api/health")
    def health() -> JSONResponse:
        state = current.snapshot()
        return JSONResponse(
            {
                "status": "ok",
                "schema_version": 1,
                "session_id": state.song.session_id,
                "launch_id": state.launch_id,
                "revision": state.revision,
                "reload_enabled": state.reload_enabled,
                "reload_error": state.reload_error,
                "score_filename": state.score_filename,
                "reloading": state.reloading,
            },
            headers={"Cache-Control": "no-store"},
        )

    @app.get("/api/song")
    def score() -> JSONResponse:
        return JSONResponse(
            jsonable_encoder(current.snapshot().song), headers={"Cache-Control": "no-store"}
        )

    return app


def _open(url: str) -> None:
    try:
        opened = webbrowser.open(url)
    except Exception:
        opened = False
    if not opened:
        print("The browser could not open automatically. Open the URL above.", flush=True)


def _server(app: FastAPI) -> PlayerServer:
    return PlayerServer(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            log_level="error",
            access_log=False,
            lifespan="off",
            timeout_graceful_shutdown=1,
        )
    )


async def _started(server: PlayerServer, task: asyncio.Task[None]) -> bool:
    """Wait for the server to accept requests; False means it was interrupted first."""
    deadline = asyncio.get_running_loop().time() + STARTUP_TIMEOUT
    while not server.started:
        if server.should_exit:
            return False
        if task.done():
            await task
            raise RuntimeError("The player server stopped before it was ready; try run() again.")
        if asyncio.get_running_loop().time() >= deadline:
            raise RuntimeError("The player server did not become ready within five seconds.")
        await asyncio.sleep(0.01)
    return not server.should_exit


async def _finish(server: PlayerServer, task: asyncio.Task[None]) -> None:
    server.should_exit = True
    if not task.done():
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=2)
        except TimeoutError:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


async def _serve(song: Song, sock: socket.socket, open_browser: bool) -> None:
    entry = discover_script()
    session = Session(song, entry)
    watcher: asyncio.Task[None] | None = None
    server = _server(create_app(song, session=session))
    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        if not await _started(server, task):
            return
        url = f"http://127.0.0.1:{sock.getsockname()[1]}"
        print(f"{song.title} — {url}", flush=True)
        print(f"Keyboard studio — {url}/studio", flush=True)
        print("Press Ctrl+C to stop the player server.", flush=True)
        if entry is not None:
            print(
                f"Save {entry.path.name} to update this player; click Play after each update.",
                flush=True,
            )
            watcher = asyncio.create_task(watch(entry, session))
        if open_browser:
            _open(url)
        await task
    finally:
        if watcher is not None:
            watcher.cancel()
            await asyncio.gather(watcher, return_exceptions=True)
        await _finish(server, task)


async def _serve_studio(sock: socket.socket, open_browser: bool) -> None:
    server = _server(create_studio_app())
    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        if not await _started(server, task):
            return
        url = f"http://127.0.0.1:{sock.getsockname()[1]}"
        print(f"daft comp studio — {url}", flush=True)
        print("Press Ctrl+C to stop the studio server.", flush=True)
        if open_browser:
            _open(url)
        await task
    finally:
        await _finish(server, task)


def _listen(port: int, serve: Callable[[socket.socket], object]) -> None:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        raise RuntimeError("Run your score as a normal Python file; an async event loop is active.")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if sys.platform == "win32":
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
            sock.listen(128)
            sock.setblocking(False)
        except OSError as error:
            raise OSError(
                f"Cannot open player port {port}: {error.strerror}. "
                "Stop the other server or use port=0."
            ) from error
        with suppress(KeyboardInterrupt):
            serve(sock)


def launch(song: Song, *, port: int, open_browser: bool) -> None:
    _listen(port, lambda sock: asyncio.run(_serve(song, sock, open_browser)))


def launch_studio(*, port: int, open_browser: bool) -> None:
    _listen(port, lambda sock: asyncio.run(_serve_studio(sock, open_browser)))
