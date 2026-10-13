"""Normalize editor text and preserve literal control captions."""


def multiline(text: str) -> str:
    """Use one newline convention without stripping student input."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def single_line(text: str) -> str:
    """Replace each logical newline with a space."""
    return multiline(text).replace("\n", " ")


def caption(text: str) -> str:
    """Escape Qt's mnemonic marker so ampersands remain visible."""
    return text.replace("&", "&&")
