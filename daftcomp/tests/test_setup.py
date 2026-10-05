"""Check the installed player without calling unfinished student functions."""

from importlib.resources import files


def test_player_setup() -> None:
    """The player imports with its dependencies and includes its browser assets."""
    # Resolving resources imports daftcomp and its FastAPI/Uvicorn dependencies.
    resources = files("daftcomp").joinpath("static")
    for filename in (
        "index.html",
        "player.js",
        "audio.js",
        "style.css",
        "daft-comp-logo.png",
        "studio.html",
        "studio.js",
        "studio-lists.js",
        "studio.css",
    ):
        assert resources.joinpath(filename).is_file(), f"Missing player asset: {filename}"
