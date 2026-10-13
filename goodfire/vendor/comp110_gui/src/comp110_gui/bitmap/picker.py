"""Choose a local PNG or JPEG through the native file picker."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from comp110_gui import validation
from comp110_gui.bitmap import bitmap
from comp110_gui.bitmap import io

if TYPE_CHECKING:
    from comp110_gui.runtime import session as session_module


def choose_bitmap(*, title: str = "Open image") -> bitmap.Bitmap | None:
    """Let the user choose an image to load as an editable bitmap.

    Call this from a GUI callback. Other facade callbacks are paused while
    the native file picker is open. Canceling leaves the image unchanged.

    Args:
        title: The title displayed by the file picker.

    Returns:
        Independent, editable image pixels, or None when the user cancels.

    Raises:
        TypeError: The title is not a string.
        RuntimeError: No application is ready, or this is not the GUI thread.
        FileNotFoundError: The selected file no longer exists.
        ValueError: The selected file is corrupt or is not a PNG or JPEG.
        OSError: The selected file cannot be read.
        MemoryError: The decoded image cannot be allocated.
    """
    from comp110_gui.runtime import state

    title = validation.string(title, "title")
    session: session_module.Session = state.require_session("choose_bitmap()")
    session.ready = False
    try:
        path: str
        _selected_filter: str
        path, _selected_filter = QtWidgets.QFileDialog.getOpenFileName(
            session.main, title, "", "Images (*.png *.jpg *.jpeg)"
        )
    finally:
        # Closing the application while the picker is open must keep it stopped.
        session.ready = not session.stopping and not session.disposed
    if not path:
        return None
    return io.load_bitmap(path)
