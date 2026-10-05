"""The supplied decoding recipe. Run this file after implementing your utilities."""

from daftcomp import add_track, run
from list_utils.encoded_song import (
    CHIP_LEAD,
    CHORD_LINE,
    COUNTERLINE,
    HATS,
    KICK,
    POP_SYNTH,
    SNARE,
    SYNTH_BASS,
)
from list_utils.utils import caesar, halftime, reverse, scale_range, shift_mutate, shift_pure


def unlock(encoded: list[int], key: int) -> list[int]:
    """Undo the locks in order to restore the part's notation."""
    unlocked: list[int] = shift_pure(encoded, -key)
    unlocked = caesar(unlocked)
    unlocked = reverse(unlocked)
    shift_mutate(unlocked, -2)
    return unlocked


def main() -> None:
    """Use all six functions to reconstruct eight synchronized tracks."""
    keys: list[int] = scale_range(128, 256, 16)
    add_track(name="Pop synth", notes=unlock(POP_SYNTH, keys[0]), voice="pulse")
    add_track(name="Chord line", notes=halftime(unlock(CHORD_LINE, keys[1])), voice="pulse")
    add_track(name="Synth bass", notes=unlock(SYNTH_BASS, keys[2]), voice="triangle")
    add_track(name="Counterline", notes=unlock(COUNTERLINE, keys[3]), voice="pulse")
    add_track(name="Chip lead", notes=unlock(CHIP_LEAD, keys[4]), voice="pulse")
    add_track(name="Kick", notes=unlock(KICK, keys[5]), voice="drums")
    add_track(name="Snare", notes=unlock(SNARE, keys[6]), voice="drums")
    add_track(name="Hats / cymbals", notes=unlock(HATS, keys[7]), voice="drums")
    run(title="Harder, Better, Faster, Stronger — Unlocked", bpm=125, steps_per_beat=4)


if __name__ == "__main__":
    main()
