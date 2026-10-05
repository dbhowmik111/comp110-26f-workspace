"""Run this file to hear a phrase, then experiment with your list utilities.

You can also use the
"""

from daftcomp import add_track, run
from list_utils.utils import scale_range, shift_mutate


def main() -> None:
    """Start with a scale, then try the variations in the exercise write-up."""
    melody: list[int] = [50, 60, 70]
    scale_range(60, 73, 2)
    add_track(name="Melody", notes=melody)
    shift_mutate(melody, 12)
    run(title="EX04 Rehearsal", bpm=120, steps_per_beat=2)


if __name__ == "__main__":
    main()
