"""Translate a resolved layout tree into parent-owned Qt widgets."""

from PySide6 import QtCore
from PySide6 import QtWidgets

from comp110_gui import base
from comp110_gui import layouts
from comp110_gui.runtime import node as node_module
from comp110_gui.runtime import types


def mount_node(
    node: node_module.Node, parent: QtWidgets.QWidget, dispatch: base.Dispatch
) -> QtWidgets.QWidget:
    """Mount one node and its children with the declared expansion policy."""
    content: types.Leaf | types.Layout = node.content
    widget: QtWidgets.QWidget
    if not isinstance(content, (layouts.Row, layouts.Column)):
        widget = content._mount(dispatch)
        widget.setParent(parent)
        return widget
    container: QtWidgets.QWidget = QtWidgets.QWidget(parent)
    layout: QtWidgets.QHBoxLayout | QtWidgets.QVBoxLayout
    if isinstance(content, layouts.Row):
        layout = QtWidgets.QHBoxLayout(container)
    else:
        layout = QtWidgets.QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    horizontal: bool = False
    vertical: bool = False
    child: node_module.Node
    for child in node.children:
        widget = mount_node(child, container, dispatch)
        layout.addWidget(widget)
        directions: QtCore.Qt.Orientation = (
            widget.sizePolicy().expandingDirections()
        )
        horizontal = horizontal or bool(
            directions & QtCore.Qt.Orientation.Horizontal
        )
        vertical = vertical or bool(directions & QtCore.Qt.Orientation.Vertical)
    policy: type[QtWidgets.QSizePolicy.Policy] = QtWidgets.QSizePolicy.Policy
    container.setSizePolicy(
        policy.Expanding if horizontal else policy.Preferred,
        policy.Expanding if vertical else policy.Maximum,
    )
    return container
