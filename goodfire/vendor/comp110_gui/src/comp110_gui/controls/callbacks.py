"""Callback signatures shared by plain controls."""

from collections.abc import Callable

type Callback = Callable[[], None]
type PointCallback = Callable[[float, float], None]
