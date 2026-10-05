"""Run this file to hear a phrase, then experiment with your list utilities."""

from daftcomp import add_track, run
from list_utils.utils import caesar, halftime, reverse, scale_range, shift_mutate, shift_pure


def main() -> None:
    """Start with a scale, then experiment with list utility variations."""
    melody: list[int] = scale_range(60, 73, 2)

    # Try different list utilities on the melody.
    shifted: list[int] = shift_pure(melody, 12)
    reversed_melody: list[int] = reverse(melody)
    slower_melody: list[int] = halftime(melody)
    encoded_melody: list[int] = caesar(melody)

    # Register the original melody and shift it up an octave.
    add_track(name="Melody", notes=melody)
    shift_mutate(melody, 12)

    run(title="EX04 Rehearsal", bpm=120, steps_per_beat=2)


if __name__ == "__main__":
    main()
