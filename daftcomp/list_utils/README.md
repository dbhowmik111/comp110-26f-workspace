---
title: "EX04 - daftcomp - List Utils"
author:
  - Kris Jordan
  - Izzi Hinks
  - Luke Aiello
page: exercises
template: overview
---

# List Utils: daftcomp Edition

Someone scrambled the band's sheet music. Your job is to build six list utility
functions that can put it back together. Along the way, you will make scales,
change pitches, and play notes at half time. Once your functions work, a secret,
supplied program will use them to unlock and play an eight-part song.

You do not need to read music or recognize the song (but it is a great song). 
The goal is to practice traversing lists with `while` loops, building new lists, 
changing an existing list, and writing tests that distinguish these behaviors.

## Allowed constructs

In `utils.py`, use variables, type annotations, arithmetic, comparisons,
`if`/`else`, `while` loops, indexing, and list literals such as `[]`.
You may call `len`, the list method `append`, and your own utility functions.
You may import `REST` and `HOLD` from `daftcomp`. Use `assert` to check required
parameter invariants, as we have practiced in class.
The supplied `NotImplementedError` lines are placeholders to replace.

If you have prior programming experience, you may be inclined to use some of
the more advanced approaches below. These are off-limits in your implementations.
We have not covered them in class, so we do not expect anyone to know or use
them for this exercise:

- Other built-in functions, including `range`, `list`, `reversed`, and `sorted`.
- `for` loops, comprehensions, generators, and recursion.
- Slices such as `notes[:]` or `notes[::-1]`.
- List methods other than `append`, including `copy`, `reverse`, and `extend`.
- Concatenating, multiplying entire lists using `+`, `*`.
- The membership operators `in` and `not in`.

You **can** use arithmetic and comparisons on individual integers. The
restrictions apply to `utils.py`; whole-list equality and `is` are encouraged
in tests. The supplied song files are already written for you.

## 0. Understand your modules

Open `list_utils` inside the **daftcomp** workspace folder. Your work goes in:

- `utils.py`: the six function implementations.
- `utils_test.py`: your unit tests.

Keep a module docstring in both files and replace each `__author__` placeholder
with your 9-digit student PID as a string. Keep the supplied function names,
parameter names, and type annotations.

The remaining files are supplied: 

* `rehearsal.py` plays a short scale. You are encouraged to record a longer piece in the keyboard studio.
* `encoded_song.py` contains the locked music, and `song.py` contains its decoding recipe. Do not edit `encoded_song.py` or `song.py` to bypass a missing function.

### Writing unit tests

For **each** of the six functions, write at least **three** meaningful tests:
two expected cases and one edge case. That is at least **18 tests you write**;
the provided example does not count. Give each test a descriptive name starting
with `test_`, a descriptive docstring, and a `-> None` return annotation.

Import functions into your test file as you need them:

```python
from list_utils.utils import scale_range, shift_mutate, shift_pure
```

The supplied test example and its import start commented out so your first
workspace setup succeeds. Uncomment them when you are ready to test
`scale_range`. A separate player setup test runs from the beginning; it does
not check your functions or count toward your 18 tests.

For every list-taking function that **returns a list**, test three separate facts:
the result has the right values, the input has not changed, and the result is a
different list object. For example, this test checks copying even when offset is
zero:

```python
def test_shift_pure_zero_offset() -> None:
    """Shifting by zero still produces an independent list."""
    original: list[int] = [60, 64]
    result: list[int] = shift_pure(original, 0)
    assert result == [60, 64]
    assert original == [60, 64]
    assert result is not original
```

`==` compares values. `is` checks whether two references point to the same object.
For `shift_mutate`, keep an alias and check that it sees the changes; also check
that the call returns `None`. Include empty inputs. For required parameter
invariants, test that invalid inputs fail an assertion using
`pytest.raises(AssertionError)`, as demonstrated below.

Run your tests from the **daftcomp** project directory:

```sh
uv run python -m pytest
```

You can also use **Daftcomp: Run EX04 Tests** from **Terminal > Run Task**,
or VS Code's Testing pane.

The tests do not open the music player. You can earn credit for good tests while
your implementation is unfinished: write tests that describe correct behavior,
not tests that expect the placeholder to raise `NotImplementedError`.

**You are encouraged to write failing tests first, then correctly implement your 
functions so that they pass!**

## 1. `scale_range(start: int, stop: int, step: int) -> list[int]`

Build a new list beginning at `start`, adding `step` each time. The stopping
boundary is **exclusive**: do not include `stop`, and do not cross it.

- With a positive step, include values less than `stop`.
- With a negative step, include values greater than `stop`.
- If the direction cannot reach the stopping boundary, return a new empty list.
- Assert that `step` is nonzero, even when `start == stop`.

```python
scale_range(60, 67, 2)  # [60, 62, 64, 66]
scale_range(67, 60, -2)  # [67, 65, 63, 61]
scale_range(60, 60, 1)  # []
scale_range(60, 67, -1)  # []
scale_range(-3, 4, 2)  # [-3, -1, 1, 3]
```

Your function works with general integers, even those outside the playable
pitch range. You are implementing the behavior with a `while` loop yourself;
do not call Python's `range` function.

To test that a parameter invariant is enforced, import `pytest` in your test file.
A failed assertion produces an `AssertionError`:

```python
def test_scale_range_zero_step() -> None:
    """A zero step is rejected instead of causing an infinite loop."""
    with pytest.raises(AssertionError):
        scale_range(60, 72, 0)
```

Test ascending and descending values, exclusive boundaries, empty results,
and the nonzero-step invariant.

**Hear it:** in `rehearsal.py`, import `scale_range` from
`list_utils.utils` and replace the supplied three-note list with
`scale_range(60, 73, 2)`. Run `uv run python list_utils/rehearsal.py`
and click **Play**.
You can also open `rehearsal.py` and use VS Code's **Run Python File** button.
Stop the Python program with Ctrl+C. Try changing the start, stop, and step in
`rehearsal.py`, keeping playable pitches between 0 and 127.

## 2. `shift_mutate(original: list[int], offset: int) -> None`

Add `offset` to **every integer** in `original`. Change the existing list by
assigning to its indices. Do not return a list; the call returns `None`.

```python
notes: list[int] = [60, 64, 67]
alias: list[int] = notes
shift_mutate(alias, 12)
# notes and alias are now [72, 76, 79].
```

The list's length stays the same. An empty list stays empty. Negative offsets
subtract from each value; offset zero leaves the values unchanged.

This function does ordinary integer arithmetic, including on negative values:
`shift_mutate([-2, -1, 60], 2)` changes that list to `[0, 1, 62]`.

Test positive and negative offsets, mutation visible through an alias, and
the `None` return. For playback, shifting a list of pitches by 12 raises it
one octave.

**Hear a reference:** in `rehearsal.py`, call `shift_mutate(melody, 12)`
**after** `add_track(...)` and **before** `run(...)`. Remember to import it.
The registered track hears the change because `add_track` retains the list
you gave it. Predict the sound before running the program.

## 3. `shift_pure(original: list[int], offset: int) -> list[int]`

Compute the same shifted values as the last function, but return them in a **new list**. 
Do not change `original`.

```python
original: list[int] = [60, 64, 67]
higher: list[int] = shift_pure(original, 12)
# higher is [72, 76, 79]. original is still [60, 64, 67].
```

This function also shifts every integer, including negative ones. An empty
input produces a new empty list. Offset zero must still produce a new list.

Test both positive and negative offsets, empty inputs, and a zero-offset copy.
Check both values and identity. A function that changes its input and then
returns it is not pure.

**Hear two parts:** register `original` with one track name and
`shift_pure(original, 12)` with another. They play at the same time. Use the
player's mute controls to hear each part separately.

## 4. `reverse(original: list[int]) -> list[int]`

Return a new list containing the original integers in the opposite order.
Do not change the input.

```python
reverse([60, 64, 67])  # [67, 64, 60]
reverse([60])  # [60], but in a new list
reverse([])  # [], but in a new list
```

Hint: the last index is `len(original) - 1`. Think about what happens when
the input is empty. Test a longer list, repeated values, and empty or one-item
lists. Check that the input is unchanged and the result is independent.

**Hear it:** reverse a scale and register it as a track.

## A little musical notation

The player reads each list entry as one equal-length time step:

| Integer | Meaning |
| --- | --- |
| `0` through `127` | Start a note with this pitch |
| `REST`, which is `-1` | Silence for this step |
| `HOLD`, which is `-2` | Continue the preceding note without starting it again |

Import `REST` and `HOLD` from `daftcomp` to use these names.
`[60, 60]` starts two notes. `[60, HOLD]` starts one note that lasts two steps.
A rest ends the current note. A playable `HOLD` must follow a note or another
hold that continues that note.

Our general integer functions do not enforce these musical rules. Shifting
`REST` changes its integer value. Reversing `[60, HOLD]` gives `[HOLD, 60]`,
which is not playable as-is. The supplied decoder restores valid notation
before registering tracks. Use HOLD-free pitch lists for your early experiments.

## 5. `halftime(original: list[int]) -> list[int]`

Return a new list that plays at **half time**: each original step lasts twice
as long, so the result has twice as many entries. Do not change `original`.

Append **each original entry**, followed by one extra entry:

- If the original entry is `REST`, append another `REST`.
- Otherwise, append `HOLD`. This also extends an existing `HOLD`.

This extends a note instead of starting it again. One traversal with a `while`
loop and `if`/`else` decisions is enough; no nested loop is needed.

```python
halftime([60, 64])  # [60, HOLD, 64, HOLD]
halftime([60, REST, 64])  # [60, HOLD, REST, REST, 64, HOLD]
halftime([60, HOLD])  # [60, HOLD, HOLD, HOLD]
halftime([60, 60])  # [60, HOLD, 60, HOLD]
halftime([])  # [], in a new list
```

Assume input entries are pitches, `REST`, or `HOLD`; you do not need to validate
their musical ordering. The player performs that validation separately.
Use this function for pitched tracks. Drum tracks do not accept `HOLD`, so the
supplied song does not apply `halftime` to drums.

Test notes, rests, existing holds, repeated pitches, and empty input. Check that
the input is unchanged and the result is a new list, even for an empty input.

**Hear it:** register `halftime(scale_range(60, 73, 2))` and compare it with your
original scale. A two-step note sounds different from two one-step notes!

## 6. `caesar(original: list[int]) -> list[int]`

A Caesar-style cipher shifts values around a fixed alphabet, wrapping around
when it reaches the end. Our alphabet is the 128 integers from 0 through 127.
Shift each of these values **64 places forward**, wrapping back to zero after
127. Copy `REST` and `HOLD` unchanged. Return a new list without changing the
input.

```python
caesar([0, 1, 63, 64, 127])  # [64, 65, 127, 0, 63]
caesar([60, HOLD, REST, 67])  # [124, HOLD, REST, 3]
caesar([])  # [], in a new list
```

Use the remainder operator `%` to wrap values. For example, on a clock with
12 positions, `(10 + 5) % 12` gives `3`.

Assume every input entry is in 0–127 or is `REST` or `HOLD`. You do not need
to validate other inputs. Shifting by 64 twice makes a full turn through
128 values, so the same function can encode and decode:

```python
caesar(caesar([60, HOLD, REST, 67]))  # [60, HOLD, REST, 67]
```

Test values on both sides of the wrap boundary, preserved special values,
and empty inputs. Also check that two applications restore the original
values without sharing its list. This is a puzzle encoding, not secure encryption.

## 7. Unlock the band

When your functions and tests are ready, run:

```sh
uv run python list_utils/song.py
```

You can also open `song.py` and use VS Code's **Run Python File** button.
The supplied `utils.py` starts with `NotImplementedError` placeholders; replace
them with your implementations before attempting the full song.

The supplied recipe generates eight keys using `scale_range`, removes each
key with `shift_pure`, applies `caesar` and `reverse`, restores the notation
using `shift_mutate`, and restores the chord line's timing with `halftime`.
You implement the tools; the recipe tells the tools how to work together.
You do not need to guess keys.

Click **Play** to hear all eight parts. This unlocks the complete 992-step
arrangement represented in this repository: about 119 seconds at 125 BPM.
The source is a Daft Punk tribute; see the [arrangement notes](../docs/harder-better-arrangement.md).

If you get an error or unexpected sound, first test your functions with small
lists. A passing song does not prove every edge case works, and a song that
cannot play yet does not erase credit for functions and tests that work.
You can inspect lists and test results without relying on hearing.

## 8. Submission and credit

Submit `utils.py` and `utils_test.py`, with your PID in each. In VS Code,
select **Terminal > Run Task > Create EX04 - Daftcomp Submission** for the
**daftcomp** folder. You can also run this from the Daftcomp project directory:

```sh
uv run python scripts/export_daftcomp_exercise.py
```

The task prints the path of a timestamped ZIP containing those two files.
Upload it to the course's EX04 assignment on Gradescope.

| Work | Points |
| --- | ---: |
| Six function implementations | 30 (5 each) |
| Your tests: two expected cases and one edge case per function | 60 (10 each) |
| Type annotations, docstrings, and author information | 10 |
| Total | 100 |

Each function's implementation is worth 3 points for expected cases and 2 for
edge cases. Its tests are worth 3 points per expected-case test and 4 for an
edge-case test. The remaining 10 points cover type correctness (4), docstrings
(4), and author PIDs (2). There are no lint/style points.

Your tests run against a correct implementation, so you can earn test credit
even if your own function is unfinished. Counted tests must pass, include an
assertion or `pytest.raises`, and call the function they test. Write separate
test functions for the two expected cases and one edge case; repeated calls or
parameterized versions of the same test do not increase this count. The supplied
starter example does not count. Staff also review whether assertions are meaningful.

Early submissions earn an additional 5 percentage points when submitted **more
than 48 hours** before the Gradescope deadline, or 3 percentage points when
submitted **more than 24 hours** before it. The bonuses do not stack. Exactly
48 hours earns 3 points; exactly 24 hours earns no bonus. Eligibility uses the
timestamp of the submission being graded and the assignment's Gradescope due date.

Required edge behavior and mutation contracts are part of function correctness.
Source review checks the allowed constructs. 