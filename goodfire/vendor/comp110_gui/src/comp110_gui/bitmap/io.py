"""Load local PNG and JPEG files into headless bitmaps."""

from __future__ import annotations

import pathlib

from PySide6 import QtCore
from PySide6 import QtGui

from comp110_gui import validation
from comp110_gui.bitmap import bitmap


def load_bitmap(path: str) -> bitmap.Bitmap:
    """Load a local PNG or JPEG, applying its orientation metadata.

    Raises:
        FileNotFoundError: The input file does not exist.
        ValueError: The file is corrupt or is not a PNG or JPEG.
        OSError: The file cannot be read.
        MemoryError: The decoded image cannot be allocated.
    """
    validation.string(path, "path")
    data: bytes = pathlib.Path(path).read_bytes()
    buffer: QtCore.QBuffer = QtCore.QBuffer()
    buffer.setData(QtCore.QByteArray(data))
    buffer.open(QtCore.QIODevice.OpenModeFlag.ReadOnly)
    reader: QtGui.QImageReader = QtGui.QImageReader(buffer)
    reader.setAutoTransform(True)
    if reader.format().data() not in (b"png", b"jpeg", b"jpg"):
        raise ValueError(f"{path!r} is not a supported PNG or JPEG image.")
    image: QtGui.QImage = reader.read()
    if image.isNull():
        raise ValueError(f"Could not decode {path!r}: {reader.errorString()}")
    rgba: QtGui.QImage = image.convertToFormat(
        QtGui.QImage.Format.Format_RGBA8888
    )
    if rgba.isNull():
        raise MemoryError(f"Could not allocate decoded pixels for {path!r}.")
    return bitmap.from_image(rgba)
