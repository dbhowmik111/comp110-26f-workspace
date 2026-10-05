"""Launch an original diagnostic song, or the keyboard studio, through the public API."""

import argparse

from . import HAT, HOLD, KICK, REST, SNARE, add_track, clear, run, studio


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the bundled daftcomp rehearsal demo.")
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["demo", "studio"],
        default="demo",
        help="demo (default) plays a short song; studio records what you play into lists.",
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="Print the URL without opening it."
    )
    parser.add_argument("--port", type=int, default=0, help="0 (automatic), or 1024 through 65535.")
    args = parser.parse_args()
    if args.mode == "studio":
        studio(open_browser=not args.no_browser, port=args.port)
        return
    clear()
    melody: list[int] = [72, HOLD, 76, 74, 67, HOLD, 72, REST, 79, 76, 74, HOLD, 72, 67, 72, HOLD]
    bass: list[int] = [48, HOLD, 55, HOLD, 53, HOLD, 55, HOLD]
    drums: list[int] = [KICK, HAT, SNARE, HAT, KICK, HAT, SNARE, REST] * 2
    add_track(name="Camp melody", notes=melody)
    add_track(name="Short bass", notes=bass, voice="triangle")
    add_track(name="Marching beat", notes=drums, voice="drums")
    run(title="Welcome to Band Camp", bpm=116, open_browser=not args.no_browser, port=args.port)


if __name__ == "__main__":
    main()
