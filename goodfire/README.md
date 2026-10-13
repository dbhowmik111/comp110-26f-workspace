# Good Fire

Wildfires are growing larger and more frequent as the climate warms. Fire
scientists and firefighters are answering with *good fire* (prescribed
burns), fuel breaks, Firewise homes, and well-timed water drops. In
Good Fire you build the software for a hands-on planning table: sketch
where people live and where rivers and roads run, then plan a fire season
that protects homes and restores habitat. (Curious where the idea came
from? See [`inspiration.md`](inspiration.md).)

* **Part 1: The Sketch Table (2D).** Read [`PART1.md`](PART1.md).

## Running things

Use **Terminal → Run Task…** in VS Code and pick a `Good Fire` task, or run
these from this folder:

```bash
uv run python app.py          # Part 1: the 2D sketch table
uv run python -m pytest checks   # the provided checks
```

## Submitting

Run the **Create Good Fire Part N Submission** task. It writes a ZIP into
this folder; upload that ZIP to Gradescope.
