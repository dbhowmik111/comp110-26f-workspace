"""The single application session and the checks guarding its lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from comp110_gui import validation

if TYPE_CHECKING:
    from comp110_gui.runtime import session as session_module

_session: session_module.Session | None = None
_launching: bool = False
_has_run: bool = False


def require_session(operation: str) -> session_module.Session:
    """Require a session that is ready to dispatch student callbacks."""
    validation.main_thread()
    if (
        _session is None
        or not _session.ready
        or _session.building
        or _session.stopping
    ):
        raise RuntimeError(
            f"{operation} requires a running application. "
            "Call it from a callback, after build() has finished."
        )
    return _session
