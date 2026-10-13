"""PROVIDED: the Good Fire sketch table, built with comp110_gui.

Run from this folder with:  uv run python app.py

You shape the scenario by hand: sketch neighborhoods, ponds, meadows,
rivers, and roads on the map, light a fire, and watch it respond. The app
only talks to your code through Landscape's methods and the Land,
Burnable, and Feature protocols.

The app runs before your code is finished. Anything that still raises
NotImplementedError("TODO: ...") is skipped, and the window tells you which
method to write next, so each part comes alive as you finish it.
"""

from collections.abc import Callable

from comp110_gui import Bitmap
from comp110_gui import Button
from comp110_gui import Callback
from comp110_gui import Canvas
from comp110_gui import Choice
from comp110_gui import Column
from comp110_gui import Label
from comp110_gui import Row
from comp110_gui import TextArea
from comp110_gui import TextBox
from comp110_gui import choose_bitmap
from comp110_gui import run

from goodfire import terrain
from goodfire.cover import Home
from goodfire.cover import Road
from goodfire.cover import Water
from goodfire.grid import Point
from goodfire.landscape import Landscape
from goodfire.photo import features_from_photo
from goodfire.plants import Grass
from goodfire.plants import Hardwood
from goodfire.plants import Pine
from goodfire.protocols import Feature
from goodfire.protocols import Land
from goodfire.sketch import Polygon
from goodfire.sketch import Polyline
from goodfire.sketchfile import read_feature
from goodfire.sketchfile import save_sketch
from goodfire.sketchfile import sketch_lines

SEED: int = 110
DEFAULT_SKETCH: str = "sketches/watershed.txt"

# Each drawing tool: (label, "area" or "line", cover)
TOOLS: list[tuple[str, str, str]] = [
    ("Sketch homes (area)", "area", "homes"),
    ("Sketch pond (area)", "area", "pond"),
    ("Sketch meadow (area)", "area", "grass"),
    ("Sketch pine stand (area)", "area", "pine"),
    ("Sketch river (line)", "line", "river"),
    ("Sketch road (line)", "line", "road"),
]


def unfinished(error: NotImplementedError) -> str:
    """Name the method that still needs code, from its TODO message."""
    name: str = str(error).removeprefix("TODO: ")
    return f"Not finished yet: {name} (see PART1.md)."


def shapes(count: int) -> str:
    """Return "1 shape" or "3 shapes"."""
    if count == 1:
        return "1 shape"
    return f"{count} shapes"


def text_or_todo(make: Callable[[], str]) -> str:
    """Return make()'s text, or a note naming the unfinished method."""
    try:
        return make()
    except NotImplementedError as error:
        return unfinished(error)


def progress(name: str, check: Callable[[], object]) -> str:
    """Run a quick check of one class; report done or what to write next."""
    try:
        check()
    except NotImplementedError as error:
        return f"{name}: write {str(error).removeprefix('TODO: ')} next"
    return f"{name}: done"


def check_cover() -> None:
    """Use each fire method you write in cover.py once, in handout order."""
    water: Water = Water(0, 0)
    water.is_home()
    water.can_ignite()
    water.is_burning()
    home: Home = Home(0, 0, False)
    home.is_home()
    home.can_ignite()
    home.ignite()
    home.is_burning()


def check_polyline() -> None:
    """Use each of Polyline's methods once."""
    line: Polyline = Polyline([Point(0.5, 0.5), Point(0.5, 3.5)], "road")
    line.length()
    str(line)
    repr(line)


def check_landscape() -> None:
    """Use each of Landscape's methods once, on a throwaway map."""
    land: Landscape = Landscape(SEED, [])
    land.ignite(22, 7)
    land.neighbors(5, 5)
    land.count_burning()
    land.homes()
    land.homes_safe()
    str(land)
    repr(land)


class SketchTable:
    """A map you can sketch on, with controls to light and step a fire."""

    features: list[Feature]
    landscape: Landscape
    pending: list[Point]
    canvas: Canvas
    tool: Choice
    status: Label
    your_code: Label
    hint: Label
    inspector: Label
    sketch_list: TextArea
    debug: TextArea
    path: TextBox
    layout: Row
    legend: Canvas

    def __init__(self):
        """Load the default sketch, grow the landscape, and build controls."""
        self.features = []
        self.pending = []
        size: int = terrain.GRID_SIZE * terrain.CELL_SIZE
        self.canvas = Canvas(
            width=size,
            height=size,
            background="black",
            alt_text="Map of the watershed. North and uphill are at the top.",
        )
        self.canvas.on_click(self.handle_click)
        options: list[str] = ["Inspect", "Light a fire"]
        label: str
        for label, _shape, _cover in TOOLS:
            options.append(label)
        self.tool = Choice(options, label="Click the map to")
        self.tool.on_change(self.tool_changed)
        self.status = Label("")
        self.your_code = Label(
            "Your code: "
            + " · ".join(
                [
                    progress("cover.py", check_cover),
                    progress("Polyline", check_polyline),
                    progress("Landscape", check_landscape),
                ]
            )
        )
        self.hint = Label("Click a square to read its str() and repr().")
        self.inspector = Label("")
        self.sketch_list = TextArea(
            label="Sketch (str of each shape)", read_only=True
        )
        self.debug = TextArea(label="Debug view (repr)", read_only=True)
        self.path = TextBox(label="Sketch file", text=DEFAULT_SKETCH)

        controls: Column = Column()
        controls.add(Label("Good Fire · Part 1 · Sketch table"))
        controls.add(self.status)
        controls.add(self.your_code)
        controls.add(self.tool)
        controls.add(self.hint)
        shape_row: Row = Row()
        shape_row.add(self.button("Finish shape", self.finish_shape))
        shape_row.add(self.button("Undo last shape", self.undo_shape))
        controls.add(shape_row)
        fire_row: Row = Row()
        fire_row.add(self.button("Step", self.step_once))
        fire_row.add(self.button("Step 10", self.step_ten))
        fire_row.add(self.button("Restart fire", self.rebuild))
        controls.add(fire_row)
        controls.add(self.path)
        file_row: Row = Row()
        file_row.add(self.button("Save sketch", self.save))
        file_row.add(self.button("Load sketch", self.load))
        file_row.add(self.button("Sketch from photo", self.from_photo))
        controls.add(file_row)
        controls.add(Label("Inspector (str)"))
        controls.add(self.inspector)
        controls.add(self.sketch_list)
        controls.add(self.debug)

        self.legend = Canvas(
            width=size,
            height=3 * terrain.CELL_SIZE + 8,
            background="#F4F1EA",
            alt_text="Legend: what each kind of square looks like.",
        )
        map_column: Column = Column()
        map_column.add(self.canvas)
        map_column.add(self.legend)
        self.draw_legend()

        self.layout = Row()
        self.layout.add(map_column)
        self.layout.add(controls)
        self.load_what_works(DEFAULT_SKETCH)
        self.landscape = Landscape(SEED, list(self.features))
        self.redraw()

    def draw_legend(self) -> None:
        """Draw one sample of each kind of square, using your own classes.

        Every sample is a different class, yet canvas.draw() treats them all
        the same way: each one only needs a draw() method (Drawable). The two
        burning homes use your Home.ignite(), so they appear once it works.
        """
        samples: list[tuple[Land, str]] = [
            (Pine(0, 0, 1.0), "Longleaf pine"),
            (Hardwood(1, 0, 1.0), "Hardwood"),
            (Grass(2, 0, 0.5), "Grass meadow"),
            (Home(0, 7, False), "Home"),
            (Home(1, 7, True), "Firewise home"),
            (Water(2, 7), "Water"),
            (self.burning_pine(Pine(0, 14, 1.0), 0), "Burning"),
            (self.burning_pine(Pine(1, 14, 1.0), 2), "Burned (survived)"),
            (Road(2, 14), "Road"),
        ]
        try:
            samples.append(
                (self.burning_home(Home(0, 21, False), 1), "Home on fire")
            )
            samples.append(
                (self.burning_home(Home(1, 21, False), 4), "Damaged home")
            )
        except NotImplementedError:
            pass  # these two appear once your Home.ignite() works
        size: int = terrain.CELL_SIZE
        cell: Land
        name: str
        for cell, name in samples:
            self.legend.draw(cell)
            self.legend.draw_text(
                name,
                (cell.col + 1) * size + 6,
                cell.row * size + 3,
                color="#2B2B2B",
                font_size=11,
            )

    def burning_pine(self, plant: Pine, steps: int) -> Pine:
        """Light a sample plant and let it burn for some steps."""
        plant.ignite()
        for _ in range(steps):
            plant.burn()
        return plant

    def burning_home(self, home: Home, steps: int) -> Home:
        """Light a sample home with your code; let it burn for some steps."""
        home.ignite()
        for _ in range(steps):
            home.burn()
        return home

    def button(self, text: str, action: Callback) -> Button:
        """Create a button that calls ``action`` when clicked."""
        made: Button = Button(text)
        made.on_click(action)
        return made

    def build(self) -> Row:
        """Return the window's layout (this makes the app a View)."""
        return self.layout

    # ----------------------------------------------------------- drawing

    def redraw(self) -> None:
        """Draw the landscape, then any shape still being sketched."""
        self.canvas.clear()
        self.canvas.draw(self.landscape)
        size: int = terrain.CELL_SIZE
        index: int
        point: Point
        for index, point in enumerate(self.pending):
            x: float = point.col * size
            y: float = point.row * size
            self.canvas.draw_circle(x, y, 4, fill="white", outline="black")
            if index > 0:
                last: Point = self.pending[index - 1]
                self.canvas.draw_line(
                    last.col * size,
                    last.row * size,
                    x,
                    y,
                    color="white",
                    width=2,
                )
        status: str = text_or_todo(lambda: str(self.landscape))
        if status.startswith("Not finished"):
            status = f"Step {self.landscape.steps}. {status}"
        self.status.set_text(status)
        lines: list[str] = []
        number: int
        feature: Feature
        for number, feature in enumerate(self.features, start=1):
            lines.append(f"{number}. {text_or_todo(feature.__str__)}")
        self.sketch_list.set_text("\n".join(lines))

    def rebuild(self) -> None:
        """Grow a fresh landscape from the seed and the current sketch."""
        self.landscape = Landscape(SEED, list(self.features))
        self.redraw()

    # ----------------------------------------------------------- events

    def current_tool(self) -> tuple[str, str, str] | None:
        """Return the selected drawing tool, or None for Inspect/Light."""
        choice: str = self.tool.get_value()
        tool: tuple[str, str, str]
        for tool in TOOLS:
            if tool[0] == choice:
                return tool
        return None

    def tool_changed(self) -> None:
        """Explain how to use the newly chosen tool."""
        self.pending = []
        tool: tuple[str, str, str] | None = self.current_tool()
        if tool is None:
            self.hint.set_text("Click a square to inspect it or light it.")
        elif tool[1] == "area":
            self.hint.set_text("Click each corner, then press Finish shape.")
        else:
            self.hint.set_text(
                "Click points along the line, then Finish shape."
            )
        self.redraw()

    def handle_click(self, x: float, y: float) -> None:
        """Inspect, light, or add a sketch point where the user clicked."""
        size: int = terrain.CELL_SIZE
        if self.current_tool() is not None:
            self.pending.append(Point(round(y / size, 1), round(x / size, 1)))
            self.redraw()
            return
        last: int = terrain.GRID_SIZE - 1
        row: int = min(int(y // size), last)
        col: int = min(int(x // size), last)
        if self.tool.get_value() == "Light a fire":
            try:
                if self.landscape.ignite(row, col):
                    self.hint.set_text(
                        f"Fire lit at row {row}, column {col}. "
                        "Press Step to watch it spread."
                    )
                else:
                    self.hint.set_text("That square cannot catch fire.")
            except NotImplementedError as error:
                self.hint.set_text(unfinished(error))
            self.redraw()
        cell: Land = self.landscape.cell_at(row, col)
        self.inspector.set_text(text_or_todo(lambda: str(cell)))
        self.debug.set_text(
            text_or_todo(lambda: repr(cell))
            + "\n\n"
            + text_or_todo(lambda: repr(self.landscape))
        )

    def finish_shape(self) -> None:
        """Turn the clicked points into a Polygon or Polyline."""
        tool: tuple[str, str, str] | None = self.current_tool()
        if tool is None:
            self.hint.set_text("Choose a Sketch tool first.")
            return
        _label, shape, cover = tool
        if shape == "area" and len(self.pending) < 3:
            self.hint.set_text("An area needs at least 3 corners.")
            return
        if shape == "line" and len(self.pending) < 2:
            self.hint.set_text("A line needs at least 2 points.")
            return
        feature: Feature
        try:
            if shape == "area":
                feature = Polygon(list(self.pending), cover)
            else:
                feature = Polyline(list(self.pending), cover)
        except NotImplementedError as error:
            self.hint.set_text(unfinished(error))
            return
        self.features.append(feature)
        self.pending = []
        self.hint.set_text(f"Added: {text_or_todo(feature.__str__)}")
        self.rebuild()

    def undo_shape(self) -> None:
        """Remove the most recent shape (or unfinished points)."""
        if self.pending:
            self.pending = []
        elif self.features:
            self.features.pop()
        self.rebuild()

    def step_once(self) -> None:
        """Advance the fire one step."""
        self.step_fire(1)

    def step_ten(self) -> None:
        """Advance the fire ten steps, then draw once."""
        self.step_fire(10)

    def step_fire(self, count: int) -> None:
        """Advance the fire some steps, stopping at unfinished code."""
        try:
            _count: int
            for _count in range(count):
                self.landscape.step()
        except NotImplementedError as error:
            self.hint.set_text(unfinished(error))
        self.redraw()

    def save(self) -> None:
        """Save the sketch as one repr() per line."""
        try:
            save_sketch(self.path.get_text(), self.features)
        except NotImplementedError as error:
            self.hint.set_text(unfinished(error))
            return
        self.hint.set_text(f"Saved {shapes(len(self.features))}.")

    def load(self) -> None:
        """Load a sketch file and regrow the landscape."""
        self.load_what_works(self.path.get_text())
        self.rebuild()

    def load_what_works(self, path: str) -> None:
        """Load each shape in a sketch file, skipping unfinished ones."""
        self.features = []
        skipped: int = 0
        note: str = ""
        text: str
        for text in sketch_lines(path):
            try:
                self.features.append(read_feature(text))
            except NotImplementedError as error:
                skipped += 1
                note = unfinished(error)
        loaded: str = f"Loaded {shapes(len(self.features))}"
        if skipped > 0:
            self.hint.set_text(f"{loaded} and skipped {skipped}. {note}")
        else:
            self.hint.set_text(f"{loaded}.")

    def from_photo(self) -> None:
        """Add shapes found in a photo of a hand-drawn map."""
        image: Bitmap | None = choose_bitmap(title="Choose a photo of your map")
        if image is None:
            return
        found: list[Feature] = list(features_from_photo(image))
        self.features.extend(found)
        self.hint.set_text(f"Found {len(found)} marker colors in the photo.")
        self.rebuild()


def main() -> None:
    """Launch the sketch table."""
    run(
        SketchTable(),
        title="Good Fire · Sketch table",
        width=1040,
        height=640,
    )


if __name__ == "__main__":
    main()
