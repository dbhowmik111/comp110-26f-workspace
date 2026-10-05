# Daftcomp — EX04: List Utils

Build six list utility functions to unlock an eight-part song. Start with the
[exercise instructions](list_utils/README.md).

## Set up and run

1. Open the repository's `workspace.code-workspace` in VS Code.
2. Run **Terminal > Run Task > Sync all workspace projects** from `support`.
   This installs Daftcomp's dependencies and creates its own `.venv`.
3. Expand the **daftcomp** folder and open `list_utils/rehearsal.py`.
4. Click **Run Python File** in the editor, then click **Play** in
   the browser. The supplied three-note phrase works before you implement
   any functions. Stop the Python program with **Ctrl+C**.

The sync task also runs a player setup test and any tests you have written.
The supplied example in `utils_test.py` starts commented out. Uncomment its
import and function when you are ready to test `scale_range`, then add your own
tests. The setup test checks the installation; it does not check your solutions
or count toward your required tests.

For terminal commands, open a terminal for the **daftcomp** folder. All commands
in these instructions run from that folder:

```sh
uv run python list_utils/rehearsal.py
uv run python -m pytest
uv run python list_utils/song.py
```

Use **Daftcomp: Run EX04 Tests** or VS Code's Testing pane to run your tests.
Use **Daftcomp: Play Unlocked Song** after implementing all six functions.
The **Run and Debug** pane offers **Daftcomp: Debug Rehearsal** and
**Daftcomp: Debug Unlocked Song** for stepping through calls with breakpoints.
You can also use **Daftcomp: Rehearsal** from **Terminal > Run Task**.
If VS Code asks for an interpreter, choose the environment in `daftcomp/.venv`.

The sync task (or `uv sync --locked` from this folder) installs the player and
its dependencies. The editable-install configuration in `pyproject.toml` adds
both this folder and `src` to the environment's Python search path, so direct
file launches can import `list_utils` and `daftcomp` from any working directory.
Run sync again after updating the project configuration.

Saving a running score updates the same browser tab. Click **Play** again to
hear it. Closing the browser does not stop Python; use **Ctrl+C** in its terminal.
The player and its assets are included, so playback needs no internet after setup.

## Files you work on

- `list_utils/utils.py`: six function skeletons to implement.
- `list_utils/utils_test.py`: your tests and one provided example.
- `list_utils/rehearsal.py`: a short phrase for experimenting with your functions.

The song decoder and encoded music are supplied. Keep `song.py` and
`encoded_song.py` unchanged. Replace the author placeholders in your two
submitted files with your 9-digit PID.

## Submit

Run **Terminal > Run Task > Create EX04 - Daftcomp Submission** for the
**daftcomp** folder. The task prints the path of a timestamped ZIP containing
only `utils.py` and `utils_test.py`. Upload it to EX04 on Gradescope.

The terminal equivalent is:

```sh
uv run python scripts/export_daftcomp_exercise.py
```
