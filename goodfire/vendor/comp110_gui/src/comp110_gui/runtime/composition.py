"""Validate content and resolve views before any native widgets exist."""

from collections.abc import Callable
from typing import cast

from comp110_gui import base
from comp110_gui import controls
from comp110_gui import graphics
from comp110_gui import layouts
from comp110_gui.runtime import node as node_module
from comp110_gui.runtime import prepared as prepared_module


def prepare(
    content: object, reserved: dict[int, str], location: str
) -> tuple[node_module.Node, prepared_module.Prepared]:
    """Resolve every view and diagnose reuse before allocating any widgets."""
    prepared: prepared_module.Prepared = prepared_module.Prepared()

    def visit(value: object, path: str) -> node_module.Node:
        identity: int = id(value)
        previous: str | None = reserved.get(
            identity, prepared.paths.get(identity)
        )
        if previous is not None:
            raise ValueError(
                f"This {type(value).__name__} appears in two places or a "
                f"cycle: {previous} and {path}. Create a second object "
                "for the second location."
            )
        prepared.paths[identity] = path
        prepared.objects.append(value)
        if isinstance(value, (layouts.Row, layouts.Column)):
            if value._disposed or value._mounted:
                raise RuntimeError("This layout has already been mounted.")
            prepared.layouts.append(value)
            node: node_module.Node = node_module.Node(value)
            index: int
            child: layouts.Content
            for index, child in enumerate(value._children):
                node.children.append(visit(child, f"{path}[{index}]"))
            return node
        if isinstance(
            value,
            (
                controls.Label,
                controls.Button,
                controls.TextBox,
                controls.Checkbox,
                controls.Choice,
                controls.TextArea,
                controls.Slider,
                graphics.Picture,
                graphics.Canvas,
            ),
        ):
            value._check_mutable()
            prepared.controls.append(value)
            return node_module.Node(value)
        build: object = getattr(value, "build", None)
        if not callable(build):
            raise TypeError(
                f"Expected a control, Row, Column, or object with build(); "
                f"received {type(value).__name__}."
            )
        result: object = cast(Callable[[], object], build)()
        if not isinstance(result, (layouts.Row, layouts.Column)):
            raise TypeError(
                f"{type(value).__name__}.build() must return a Row or "
                f"Column; received {result!r}."
            )
        return visit(result, f"{path}.{type(value).__name__}.build()")

    return visit(content, location), prepared


def check_content(content: object) -> None:
    """Reject unsupported content without building or mounting a view."""
    if not isinstance(content, (base.Control, layouts.Row, layouts.Column)):
        if not callable(getattr(content, "build", None)):
            raise TypeError(
                "Expected a control, Row, Column, or object with build(). "
                "A Window, Bitmap, or Color cannot be used as content."
            )
