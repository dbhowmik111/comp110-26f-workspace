# Good Fire — Part 1: The Sketch Table

**Due Tuesday, October 13, at 9:00 pm** on Gradescope.

## The story

Fire belongs in many landscapes. North Carolina's longleaf pine savannas
evolved with low, creeping fires every two to three years; their wiregrass
will not even reseed without fire. Today, fire managers at places like the
NC Forest Service and The Nature Conservancy light *prescribed* fires on
purpose, in mild weather, to keep these forests healthy. A prescribed fire
burns off **fuel**: anything that can burn, such as dry grass, fallen pine
needles, dead leaves, and brush. Fuel that builds up for years would
otherwise feed a dangerous wildfire.

Climate change is stretching fire-weather seasons longer and drier, including
here in the Southeast, while more people build homes where neighborhoods
meet the woods. That makes good planning more important than ever.

In this project you build a **sketch table**: a map of a small watershed
that you can draw homes, roads and rivers on, then start a fire to see what happens. In Part 1, you write the code for the objects on the map, the shapes people sketch, and
the rules for how fire moves. In Part 2, you will add fire
management strategies.

Curious where the idea came from? `inspiration.md` tells the story of the
research tool that inspired this project. You don't need it to do the
assignment.

## How the map works

Read this section before you start coding. Everything in your tasks builds
on these ideas.

### The grid: 30 x 30 squares

The map is a grid of **30 rows and 30 columns**. Each square represents a
**30 meter by 30 meter** patch of land on Earth. That is the same size of square that LANDFIRE, the
national fuel maps from the US Forest Service and the Department of the
Interior, uses to describe fuel across the country.

Rows are numbered 0 to 29 from north (the top) to
south. Columns are numbered 0 to 29 from west (left) to east (right).

Two small provided classes in `grid.py` name places on the map:

* **`Square(row, col)`** is one whole square of the grid. Its `row` and
  `col` attributes are `int`s. For instance, `Square(2, 11)` is the square in row 2,
  column 11.
* **`Point(row, col)`** is an exact spot on the map, like the place where
  someone clicks. Its `row` and `col` attributes are `float`s. For instance, `Point(2.5, 11.0)` is two and a half squares down from the north edge and 11 squares in
  from the west edge. Shapes that people sketch are made of `Point` objects.

Both of these classes work like CL16's `Point` class: read their attribute's values with `.row` and `.col`. For example, `Point(2.5, 11.0).row` is `2.5`, and `Square(2, 11).col` is `11`.

### Steps: how time passes

The simulation moves forward in **steps**, like turns in a board game. In
one step, every burning square gets one chance to spread fire to its
neighbors, and then burns a little longer. When we say, "a home burns for 4 steps," we mean a home stays on fire for four turns of the simulation and then burns out. On the other hand, 
grass burns out after just one step. A square that is burning keeps count
of the steps it has left in its `time_left` attribute. In the graphical user interface (GUI), the **Step** button moves the fire forward one step.

(These instructions also use "Step" for the parts of your work: Step 1
through Step 4 under "Your tasks". When a Step has a number and a heading,
it means a part of the assignment; everywhere else, a step is one turn of
the fire.)

### What a square can hold: six land cover types

Every square of the grid holds exactly one object, and that object is the
square's **land cover**: what is on that patch of ground. There are six land cover types:

| Land cover | Class (file) | What it is | Can it burn? | Burns for |
| --- | --- | --- | --- | --- |
| Longleaf pine | `Pine` (`plants.py`) | the pine savanna that covers most of the hills | yes | 2 steps |
| Hardwood | `Hardwood` (`plants.py`) | damp leafy forest along the river | yes | 3 steps |
| Grass | `Grass` (`plants.py`) | an old meadow | yes | 1 step |
| Home | `Home` (`cover.py`) | one house | yes | 4 steps |
| Water | `Water` (`cover.py`) | a river or pond | never | never |
| Road | `Road` (`cover.py`) | pavement | never | never |

The three vegetation classes are the fuel a
wildfire can run through. Homes are objects we always want to protect. Water and roads
can never burn, so they stop a fire from spreading where they cross its path. Fire crews
use rivers and roads this way as ready-made **fuel breaks**: lines with
nothing to burn.

All six classes fit the same **protocol**, `Land` (in `protocols.py`). As
in CL18, a protocol lists the attributes and methods an object must have;
any class that has all of them specifies the protocol. Every
`Land` object has `row` and `col` attributes, `color()` and `draw()` methods for the map,
and the same seven methods pertaining to fire:

| Method | Meaning |
| --- | --- |
| `is_fuel()` | could this square ever burn? (plants and homes: `True`) |
| `is_home()` | is this square a home? |
| `can_ignite()` | could this square catch fire right now? |
| `ignition_chance()` | how likely one burning neighbor is to light it, from 0.0 to 1.0 |
| `ignite()` | start burning |
| `burn()` | burn for one step |
| `is_burning()` | is it on fire right now? |

Water and roads should return `False`
for the `is_fuel()`, `is_home()`, `can_ignite()`, and `is_burning()` methods; `0.0` for `ignition_chance()`; and their `ignite()`
and `burn()` methods do nothing. Because every square object has these same methods,
the rest of the program can ask any square what it can do without ever checking which class it is.

Each kind of fuel catches and burns at its own rate, based on a published
fire-spread model. The provided code handles all of that for you, so you
don't need it for your tasks. If you are curious, `fire_science.md`
explains how it works (optional).

## Step 0: Setup

This project lives in your COMP110 workspace as the `goodfire` folder.

1. Run the workspace's **Sync all workspace projects** task (see
   `support/README.md`).
2. Open `goodfire` and use **Terminal → Run Task…**:
   * **Good Fire: Sketch Table (2D)** runs `app.py`.

   Or, in a terminal in the `goodfire` folder: `uv run python app.py`.

   The app runs from the very start, even before you write any code. It
   shows the map of pines, hardwoods, and meadow, and skips anything that
   is not finished yet. Under the status line, **Your code** tells you
   which class to work on and which method to write next, for example
   `cover.py: write Water.is_home next`. As you finish each method, another
   part of the app comes alive. Close the app and run it again after you
   change your code. The checks tell you exactly what is left.

## Files

You will write code in three Python modules (files). You don't need to read every other file:
the table says which ones you will use. The rest are there for the app
to work, and for you to explore if you're curious. 

| File | What you do with it | What it holds |
| --- | --- | --- |
| **`goodfire/cover.py`** | **write code here** | `Home`, `Water`, `Road` |
| **`goodfire/sketch.py`** | **write code here** | `Polygon`, `Polyline` |
| **`goodfire/landscape.py`** | **write code here** | `Landscape` |
| `goodfire/protocols.py` | read: your classes fit these | the `Land` and `Feature` protocols |
| `goodfire/terrain.py` | use: you need `GRID_SIZE` | the shape of the hills and what grows where |
| `goodfire/grid.py` | optional (these instructions explain them) | `Point` and `Square` |
| `goodfire/plants.py` | optional | `Grass`, `Pine`, `Hardwood`: the plants and how they burn |
| `goodfire/science.py` | optional | the model's published numbers and small helpers (the provided code uses them) |
| `goodfire/grow.py`, `goodfire/dice.py` | optional | building the right object for each square; seeded random numbers |
| `goodfire/photo.py`, `goodfire/sketchfile.py` | optional | photo sketches; saving and loading sketches |
| `goodfire/paint.py` | optional | how each kind of square looks on the map (the `draw()` methods call it) |
| `app.py` | run it | the sketch-table window |
| `checks/check_part1.py` | run it; read a test when it fails | checks you can run any time |

Every file you hand in needs a module docstring, `__author__` set to your
9-digit PID, and type annotations on every parameter and return value
(except `__init__`, which has no return type specified, as in class).

## Your tasks

Your three files already contain some finished code. In these
instructions, each method is labeled one of two ways:

* **✏️ Your Turn:** you write this method. In your file, its body is
  `raise NotImplementedError("TODO: ...")`; replace that line with your
  code.
* **📖 For Reference:** this method is finished. Read it: it is a worked
  example, and your methods call it or follow its pattern.

Here is every method you will write, in order. Run `uv run python -m pytest checks` after each
step.

| Step | File | Your Turn |
| --- | --- | --- |
| 1 | `cover.py` | `Water.is_home`, `Water.can_ignite`, `Water.is_burning`; then `Home.is_home`, `Home.can_ignite`, `Home.ignite`, `Home.is_burning` |
| 2 | `sketch.py` | `Polyline.__init__`, `Polyline.length`, `Polyline.__repr__` |
| 3 | `landscape.py` | `Landscape.ignite`, `Landscape.neighbors`, `Landscape.homes`, `Landscape.homes_safe` |

Each method you write is an important piece of the codebase, and together they make the
whole app work. 

In Steps 1-3, the examples show calls and what they return. A line like
`h.can_ignite()  ->  True` means "calling `h.can_ignite()` returns `True`".
Try them yourself in the Python REPL (`uv run python`, then
`from goodfire.cover import Home`) or in a test.

### Step 1: `Home`, `Water`, and `Road` (`cover.py`)

`cover.py` holds the three kinds of square that people add to a
landscape: homes, water, and roads. They share no code, but all three fit
the `Land` protocol, so all three have the same methods (see "What a
square can hold" above). The difference is in what those methods do:
water and roads never burn, and a home can.

#### ✏️ Your Turn: `Water` (with `Road` For Reference)

Read these two classes first. `Road` is finished, and `Water` is almost finished. Your job is to finish implementing the following methods in `Water`:

* `is_home(self)`: is this square a home?
* `can_ignite(self)`: could this square catch fire right now?
* `is_burning(self)`: is this square on fire right now?

Water and roads never burn, so you should only need to add one line of code to complete these methods (use
`Road`'s for reference). Example method calls and return values are below:

```text
r: Road = Road(5, 5)
r.is_home()          ->  False
r.can_ignite()       ->  False
r.ignite()                       (does nothing)
r.is_burning()       ->  False
Water(8, 3).is_home()     ->  False
Water(8, 3).can_ignite()  ->  False
Water(8, 3).is_burning()  ->  False
```

#### 📖 For Reference: `Home.__init__`, `__str__`, `__repr__`, `is_fuel`, `color`, `draw`

Unlike water
and roads, a home keeps track of its own fire status in two attributes that
`__init__` sets up:

* `state` is `"safe"` at first, `"burning"` while on fire, and `"damaged"`
  after the fire burns out.
* `time_left` is how many more steps the home will burn. It is `0` while
  the home is safe.

A home also stores `row`, `col`, `hardened`, and `fuel` (always `1.0`). A
*hardened* home has been through the Firewise program: ember-resistant
vents, a clean roof and gutters, and nothing that burns within 5 feet of
the walls. That makes it much harder to ignite, because most homes lost
in wildfires are lit by flying embers, not by the flames themselves.

`__str__` reads `state` and `time_left`, so it changes as your methods
change them. That makes it a handy way to check your work:

```text
h: Home = Home(2, 11, False)
h.state      ->  "safe"
h.time_left  ->  0
str(h)       ->  "Home at row 2, column 11: safe"
str(Home(2, 12, True))   ->  "Home at row 2, column 12 (Firewise): safe"
repr(Home(2, 12, True))  ->  "Home(row=2, col=12, hardened=True)"
(burning, 4 steps left)  ->  "Home at row 2, column 11: on fire (4 steps left)"
(after it burns out)     ->  "Home at row 2, column 11: damaged"
```

#### 📖 For Reference: `burn(self)`

`burn()` is called once per step while the home burns. It takes one step
off `time_left`, and when no time is left, `state` becomes `"damaged"`.
It returns nothing. Notice that it expects `ignite()`, which you write
next, to have set `time_left` first.

Now write the four `Home` methods that let a home catch fire. (Hopefully, no homes will catch fire and they will never need to be called!)

#### ✏️ Your Turn: `is_home(self)`

Answers "is this square a home?" for a `Home` object. The `Landscape` uses it to
count homes without ever checking which class a square is.

(Hint: Compare this to the `Road` and `Water` class' `is_home` methods -- you will only need to write one line of code for this method!)

```text
Home(2, 11, False).is_home()   ->  True
```

#### ✏️ Your Turn: `can_ignite(self)`

Answers "could this home catch fire right now?" Only a safe home can catch fire, so this method should only return `True` if the state of the home is `"safe"`. A
home that is already burning, or already damaged, cannot catch again.
You will have to use `self.state`.

```text
Home(2, 11, False).can_ignite()   ->  True
(while burning)                   ->  False
(after it is damaged)             ->  False
```

#### ✏️ Your Turn: `ignite(self)`

`ignite()` starts the fire: the home object's `state` should become `"burning"` and `time_left`
should be assigned `4`, because a home burns for 4 steps. It returns nothing. 

Then, the provided `burn()` method counts the `time_left` down by one each time the Step button is pressed in the GUI. 

Here is example usage of the ignite() method (which you implement) and the burn() method (provided):

```text
h: Home = Home(2, 11, False)
h.ignite()     # state "burning", time_left 4
h.burn()       # time_left 3
h.burn()       # time_left 2
h.burn()       # time_left 1
h.burn()       # time_left 0, state "damaged"
```

#### ✏️ Your Turn: `is_burning(self)`

Answers "is this home on fire right now?" Similarly to the `can_ignite()` method, this method will expect you to use `self.state` to check if the home's state is `"burning"`.

```text
Home(2, 11, False).is_burning()   ->  False
(after ignite())                  ->  True
(after it is damaged)             ->  False
```

The plants in `plants.py` burn the same way with their own numbers, so
you can read them as more examples.

#### See it in the app

Run `uv run python app.py` again. The **Your code** line should now say
`cover.py: done`. Look at the legend under the map: two new samples have
appeared, **Home on fire** and **Damaged home**. The app made a home,
called your `ignite()`, then let `burn()` run one time (on fire) or four
times (damaged); what you see is your code at work. (Lighting real fires on the
map needs the `Landscape`, which you will complete in Step 3.)

### Step 2: sketch shapes (`sketch.py`)

Why sketch on a map? Planners, fire crews, and neighbors often ask "what
if?" What if a new neighborhood is built at the edge of the pines? What if
a road is cut between the meadow and the homes? Would it stop a fire? The
sketch table lets anyone answer these questions by drawing: click a few
points to draw a shape, choose what it is (homes, a pond, a river, a
road), and the map changes to match. This allows you to run simulations on maps with different layouts!

A sketched shape's most important job is to say which squares of the map
it covers, as a list of `Square`s, in its `squares()` method. The
`Landscape` uses that list to put homes, ponds, rivers, and roads onto the
grid. There are two kinds of shape:

* a **`Polygon`** is an *area*, outlined by its corners: a neighborhood, a
  pond, a meadow;
* a **`Polyline`** is a *line*, drawn point to point: a river or a road.

Both fit the `Feature` protocol: each has a `cover` (what the shape
becomes, like `"homes"` or `"river"`) and a `squares()` method.

#### 📖 For Reference: `Polygon`

The whole class is finished; it is your model for `Polyline`. Read how:

* `__init__` stores the list of corner `Point`s and the cover;
* `contains(row, col)` answers whether a spot is inside the shape (it uses
  a classic trick called ray casting);
* `squares()` checks the center of every square on the map with two nested
  `while` loops, and lists the squares whose centers are inside;
* `__str__` and `__repr__` describe it for people and for Python.

```text
homes: Polygon = Polygon(
    [Point(2.0, 11.0), Point(2.0, 19.0), Point(5.0, 19.0), Point(5.0, 11.0)],
    "homes",
)
homes.contains(3.5, 15.5)   ->  True
homes.contains(6.5, 15.5)   ->  False
len(homes.squares())        ->  24             (3 rows x 8 columns)
homes.squares()[0]          ->  Square(2, 11)
homes.squares()[23]         ->  Square(4, 18)
str(homes)   ->  "homes area with 4 corners covering 24 squares"
repr(homes)  ->  "Polygon([Point(2.0, 11.0), Point(2.0, 19.0), Point(5.0, 19.0), Point(5.0, 11.0)], cover='homes')"
```

Notice how `__repr__` works: a list inside an f-string shows each item's
`repr()`, so `f"{self.corners}"` prints the `Point(...)`s for you. You will
do the same in `Polyline`.

#### `Polyline`: a line through any number of points

A `Polyline` connects a list of `Point`s in order, with a straight segment
between each pair of neighboring points. With two points it is one
straight line. With more points it can bend and wind as much as you like,
the way a river does. Its `squares()` method is provided (For Reference):
it walks along every segment and lists each square the line passes
through.

```text
river: Polyline = Polyline(
    [Point(1.5, 1.5), Point(1.5, 6.5), Point(4.5, 9.5), Point(8.5, 9.5)],
    "river",
)   # three segments: east, then south-east, then south
```

#### ✏️ Your Turn: `Polyline.__init__(self, points, cover)`

Initialize the attributes of a Polyline object to the list of points and the cover parameters' values, just as `Polygon.__init__` stores
its corners.

#### ✏️ Your Turn: `Polyline.length(self)`

Returns the total length of the line, measured in squares: the sum of the
lengths of all its segments. One segment from point `a` to point `b` is
`((b.row - a.row) ** 2 + (b.col - a.col) ** 2) ** 0.5` long, just like
`get_length()` in CL16's `Line` class. A line with *n* points has *n − 1*
segments.

_Hint_: Declare a local variable to keep track of a running total. Use an index to loop through `self.points`, measuring the length of the segment from each point to the next, and adding each segment’s length to the running total.

For example, with 3 points there are 2 segments: from `self.points[0]` to
`self.points[1]`, and from `self.points[1]` to `self.points[2]`. The last
segment *starts* at index 1, which is `len(self.points) - 2`, so your loop
should stop before index `len(self.points) - 1`.

```text
road: Polyline = Polyline([Point(5.5, 0.0), Point(5.5, 10.0)], "road")
road.length()   ->  10.0

bend: Polyline = Polyline([Point(0.5, 0.5), Point(0.5, 4.5), Point(3.5, 4.5)], "river")
bend.length()   ->  7.0      (4.0 east, then 3.0 south)

slant: Polyline = Polyline([Point(0.0, 0.0), Point(3.0, 4.0)], "road")
slant.length()  ->  5.0      (a 3-4-5 triangle)
```

#### 📖 For Reference: `Polyline.__str__(self)`

`__str__` (finished) describes the line for the app's sketch list, in
meters. Read it: it calls your `length()`, and each square is 30 m, so
the provided `science.meters(squares)` converts a length in squares to
whole meters.

```text
science.meters(10.0)  ->  300
str(road)    ->  "road line 300 m long covering 11 squares"
str(bend)    ->  "river line 210 m long covering 8 squares"
```

(The road covers 11 squares, not 10, because it ends exactly on the edge of
square (5, 10).)

#### ✏️ Your Turn: `Polyline.__repr__(self)`

Returns the code that rebuilds the line, like `Polygon`'s `__repr__`
does. Look at how `Polygon.__repr__` puts a list of points in an
f-string.

```text
repr(road)   ->  "Polyline([Point(5.5, 0.0), Point(5.5, 10.0)], cover='road')"
```

#### See it in the app

Run the app again. The **Your code** line should now say `Polyline: done`, and
the default sketch's river and county road appear on the map: until now,
the app had to skip them, because they are `Polyline`s. The **Sketch** list
on the right shows each shape's `str()`, with your lengths:
`river line 949 m long covering 34 squares`.

Then, sketch your own line:

1. Choose **Sketch road (line)** from the menu above the map.
2. Click two or more points on the map, then press the **Finish shape** button. Try
   several points to make a road with bends.
3. Your road appears, and the message under the menu reads, for example,
   `Added: road line 300 m long covering 11 squares`.

To see your `__repr__`, change the **Sketch file** box to
`sketches/mine.txt`, press **Save sketch**, and open that file in VS Code.
Each line is one shape's `repr()`, and it is Python: **Load sketch** runs
those lines to rebuild your shapes. (Saving to a new file keeps the default
sketch, `sketches/watershed.txt`, unchanged.)

### Step 3: the `Landscape` (`landscape.py`)

A `Landscape` is the whole map: the 30 x 30 grid of squares, the shapes
sketched on it, and the rules for how fire moves across it. It stores the
grid in `self.grid`, a list of 30 rows, where each row is a list of 30
squares. So `self.grid[row][col]` is the object in that square: a `Pine`,
a `Home`, a `Water`, a `Road`, and so on.

Finish Step 2 before you start this step: the tests and the autograder
build their landscapes with sketched rivers and roads, so until your
`Polyline` works, every `Landscape` check reports
`not finished yet: TODO: Polyline.__init__`.

When every square in `self.grid` needs to be visited,  nested `while` loops are used; one loop over the rows of
`self.grid`, and one over the squares in each row, the way
`burned_fraction()` and `draw()` do. You never need to ask what class a
square is: every square fits the `Land` protocol, so you can call
`is_burning()`, `can_ignite()`, `is_home()`, and the rest of the methods on any of them.

The examples in this step use one landscape: the neighborhood from Step 2
plus a river across the map.

```text
river: Polyline = Polyline([Point(9.5, -0.5), Point(9.5, 30.5)], "river")
land: Landscape = Landscape(110, [river, homes])
```

The `110` is a *seed* for the random numbers (fuel loads and dice rolls):
the same seed always grows the same landscape and burns the same fire.

#### 📖 For Reference: `__init__`, `apply`, `cell_at`, `catches`, `burned_fraction`, `homes_total`, `__str__`, `__repr__`, `draw`

These are finished. `__str__` and `__repr__` are explained after
`homes_safe()` below, because they need your methods. The
ones you will use:

```text
land.cell_at(22, 7)      ->  the object at row 22, column 7 (grass in the meadow)
land.catches(neighbor)   ->  True or False: one roll of the dice, using the neighbor's ignition_chance()
land.burned_fraction()   ->  0.0 to 1.0: how much of the fuel has burned
land.homes_total()       ->  24   (it is len(self.homes()), so it needs your homes())
```

#### ✏️ Your Turn: `ignite(self, row, col)`

Starts a fire on one square (at a particular `row` and `column`), the way someone lights a fire in the app. If
the square _can_ ignite right now, set it on fire and return `True`.
Otherwise leave it alone and return `False`.

Hint: get the square's object with `self.grid[row][col]`. That object
fits the `Land` protocol, so it can answer `can_ignite()` and it has its
own `ignite()` method. Your job is to ignite the square if it can ignite.

```text
land.ignite(9, 4)    ->  False   (row 9 is the river; water cannot burn)
land.ignite(22, 7)   ->  True    (the meadow grass catches)
land.ignite(22, 7)   ->  False   (it is already burning)
```

#### ✏️ Your Turn: `neighbors(self, row, col)`

Returns a `list[Land]` of squares right next to one square: the ones directly
north, south, west, and east, **in that order**. Fire can only spread to
these four (do not include diagonals). North is one row up (`row - 1`), south is one row down
(`row + 1`), west is one column left (`col - 1`), and east is one column
right (`col + 1`).

Squares on the edge of the map have fewer neighbors: leave out any
neighbor whose row or column would be off the map (a row or col below 0, or `terrain.GRID_SIZE` or greater). For example, a corner square has only two neighbors.

Your starter code already adds the north and south neighbors; the south
check shows how to use `terrain.GRID_SIZE` to stay on the map. Add west
and east the same way, then `return result`.

```text
land.neighbors(15, 15)  ->  [object at (14, 15), object at (16, 15), object at (15, 14), object at (15, 16)]
land.neighbors(0, 0)    ->  [object at (1, 0), object at (0, 1)]                      (no north, no west)
land.neighbors(29, 5)   ->  [object at (28, 5), object at (29, 4), object at (29, 6)]  (no south)
len(land.neighbors(0, 29))   ->  2
```

#### 📖 For Reference: `count_burning(self)`

Returns how many squares on the whole map are on fire right now. The
status line uses it, and the fire is out when it reaches 0.

Read it closely: it is your model for `homes()` below. It starts a count
at 0, visits every square with two nested `while` loops (an outer loop
over the rows, an inner loop over the squares in each row), and adds 1
for each square whose `is_burning()` is `True`.

```text
land.count_burning()   ->  0     (nothing is lit yet)
land.ignite(22, 7)
land.count_burning()   ->  1     (just the meadow square)
land.step()
land.count_burning()   ->  2     (the fire spread to its neighbors)
Landscape(7, []).count_burning()   ->  0
```

#### 📖 For Reference: `step(self)`

`step()` moves the fire forward by one step of time. It is the heart of the
simulation. It uses your `neighbors()` and the fire methods every square
has (including the ones you wrote for `Home`). (Note, you would not be expected to write a method like this on a quiz!)

#### ✏️ Your Turn: `homes(self)`

Returns a `list[Land]` of every square on the map that is a home, in row order
(row 0 first, and west to east within a row). The status line and
`homes_total()` and `homes_safe()` will use it.

Hint: draw inspiration from `count_burning()`: start with an empty list instead of a
count, visit every square with the same two nested `while` loops, and
`append` each square whose `is_home()` is `True`. Append the
square's object itself, so callers can ask each home questions later.

```text
len(land.homes())       ->  24   (the 3 x 8 neighborhood)
str(land.homes()[0])    ->  "Home at row 2, column 11: safe"
str(land.homes()[23])   ->  "Home at row 4, column 18: safe"
Landscape(7, []).homes()  ->  []    (no homes were sketched)
```

#### ✏️ Your Turn: `homes_safe(self)`

Returns how many homes have not caught fire: the homes that can still
ignite. A burning or damaged home is no longer safe.

Hint: you already wrote `homes()`. Loop over the list it returns with a
`while` loop and count the homes whose `can_ignite()` is `True`. You do not
need to walk the whole grid again.

```text
land.homes_safe()              ->  24   (before any home burns)
Landscape(7, []).homes_safe()  ->  0    (no homes at all)
```

To see the number go down, put homes right next to the meadow and light
it:

```text
near: Polygon = Polygon(
    [Point(18.0, 12.0), Point(18.0, 15.0), Point(21.0, 15.0), Point(21.0, 12.0)],
    "homes",
)
land2: Landscape = Landscape(110, [river, homes, near])
land2.ignite(22, 7)
(after 6 steps)    land2.homes_safe()  ->  33   (of 33 homes)
(after 7 steps)    land2.homes_safe()  ->  32   (the fire reached the first home)
(after 10 steps)   land2.homes_safe()  ->  30
```

#### 📖 For Reference: `__str__(self)`

The status line shown above the map. It is finished, but it only works
once your methods do: it calls `count_burning()` (which asks every square
your `is_burning()`), your `homes_safe()`, and `homes_total()`, which
uses your `homes()`. It reports the step, how many squares
are burning, the percent of fuel burned (the provided
`science.percent(fraction)` turns `burned_fraction()` into a whole
percent), and how many homes are safe out of how many there are.

```text
str(Landscape(110, [river, homes]))  ->  "Step 0: 0 burning, 0% of fuel burned, 24 of 24 homes safe"
(after 3 steps of the fire above)   ->  "Step 3: 6 burning, 1% of fuel burned, 24 of 24 homes safe"
science.percent(0.256)              ->  26
```

#### 📖 For Reference: `__repr__(self)`

The code that rebuilds this landscape: its seed and its list of features
(the sketched shapes).

```text
repr(Landscape(7, []))     ->  "Landscape(seed=7, features=[])"
repr(land)                 ->  "Landscape(seed=110, features=[Polyline([Point(9.5, -0.5), ...], cover='river'), Polygon([...], cover='homes')])"
```

#### See it in the app

Run the app again. The **Your code** line says `Landscape: done`, and the
status line above it is the provided `__str__`, now counting with your
methods:
`Step 0: 0 burning, 0% of fuel burned, 24 of 24 homes safe`. Now light a
fire:

1. Choose **Light a fire** from the menu, then click the yellow meadow in
   the south-west. The message reads, for example, `Fire lit at row 22,
   column 7. Press Step to watch it spread.` (that is your `ignite()`
   returning `True`).
   Click the river: `That square cannot catch fire.` (it returned `False`).
2. Press **Step** a few times, then **Step 10**. Each press runs the
   provided `step()`, which spreads the fire through your `neighbors()`.
   Watch the status line count the burning squares and the homes still
   safe.
3. Watch the fire stop at the river and the road, and see whether it
   reaches the homes uphill.
4. Choose **Inspect** and click a burning square to read its `str()`.
   The river and road usually keep this fire away from the homes, so to
   watch a home burn, choose **Sketch homes (area)** and sketch a few homes
   in the pines right next to the meadow, then light the meadow again.
   Inspect a burning home: `Home at row 20, column 12: on fire (2 steps
   left)`, which changes each time `burn()` runs. The debug view
   below shows the `Landscape`'s `repr()`, including your new homes.
5. **Restart fire** grows the same landscape again, so the same fire
   burns the same way every time.

### Optional: Sketch different scenarios!

Now experiment. Run `uv run python app.py`.

* Choose a **Sketch** tool, click corners or points on the map, then press
  **Finish shape**. Try a neighborhood, a pond, or a winding road.
* Choose **Light a fire**, click the meadow, and press **Step**. Watch the
  river, pond, and road stop the fire, and watch which homes it reaches.
* Can you save the neighborhood? Sketch a road or a pond between the
  meadow and the homes as a fuel break, light the same fire, and compare
  how many homes stay safe. (Part 2 turns this into a real challenge.)
* Choose **Inspect** and click any square to see its `str()` and `repr()`.
* **Save sketch** writes one `repr()` per line. Open the file in VS Code:
  it is Python. **Load sketch** runs it to rebuild your shapes.
* Extension: **Sketch from photo**. Draw on white paper with markers (blue
  river or pond, red homes, black roads, yellow meadow), photograph it, and
  load the photo. The provided `PhotoSketch` fits the same `Feature`
  protocol as your shapes, so your `Landscape` handles it unchanged.

## Testing and submitting

Run **Terminal > Run Task... > Create EX05 - Good Fire Part 1 Submission** task. It writes a ZIP
  with `goodfire/cover.py`, `goodfire/sketch.py`, and `goodfire/landscape.py`
  into the `goodfire` folder; upload that ZIP to EX05 on Gradescope.

## Sources

Alexandridis et al. (2008), "A cellular automata model for forest fire
spread prediction: the case of the wildfire that swept through Spetses
Island in 1990," *Applied Mathematics and Computation* 204(1); USDA Forest
Service and US Geological Survey, LANDFIRE; IBHS (2019) on ember
ignitions; NFPA Firewise USA; The Nature Conservancy and NC Forest Service
on longleaf pine and prescribed fire; EPA Climate Change Indicators:
Wildfires.
