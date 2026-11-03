# Good Fire

Wildfires are growing larger and more frequent as the climate warms. Fire
scientists and firefighters are answering with *good fire* (prescribed
burns), fuel breaks, Firewise homes, and well-timed water drops. In
Good Fire you build the software for a hands-on planning table: sketch
where people live and where rivers and roads run, then plan a fire season
that protects homes and restores habitat. (Curious where the idea came
from? See [`inspiration.md`](inspiration.md).)

* **Part 1: The Sketch Table (2D).** Read [`PART1.md`](PART1.md).
* **Part 2: Plan the Fire Season (3D).** Read [`PART2.md`](PART2.md).

## Running things

Use **Terminal → Run Task…** in VS Code and pick a `Good Fire` task, or run
these from this folder:

```bash
uv run python app.py          # Part 1: the 2D sketch table
uv run python -m pytest checks   # the provided checks
```

```bash
uv run python app3d.py                  # Part 2: your plan in 3D
uv run python app3d.py --hotter-drier   # the same season, hotter and drier
uv run python compare_plans.py          # compare the five plans
```

## Submitting

Run the **Create Good Fire Part N Submission** task. It writes a ZIP into
this folder; upload that ZIP to Gradescope.
