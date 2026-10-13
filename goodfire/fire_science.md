# How the fire works

*Optional reading: you don't need any of this to do the assignment. The
provided code already does everything described here.*

## How each land cover burns

| Land cover | Class (file) | Can it burn? | Burns for |
| --- | --- | --- | --- |
| Longleaf pine | `Pine` (`plants.py`) | yes, at an average rate | 2 steps |
| Hardwood | `Hardwood` (`plants.py`) | yes, but slowly (damp leaf litter) | 3 steps |
| Grass | `Grass` (`plants.py`) | yes, quickly (dry grass) | 1 step |
| Home | `Home` (`cover.py`) | yes, a bit less easily than plants | 4 steps |
| Water | `Water` (`cover.py`) | never | never |
| Road | `Road` (`cover.py`) | never | never |

## Fuel

**Fuel** is anything that can burn, such as grass, leaves, or a house. A
square's **fuel load** describes how much burnable material it has. Different
materials have different fuel loads. If you are curious about the fuel loads
used for each plant, read `goodfire/plants.py`.

## How fire spreads: the Alexandridis formula

How likely is a fire to spread from one square to the next? Scientists answer
this with fire-spread models. We use the model of **Alexandridis and
colleagues (2008)**, who built it to recreate a real 1990 wildfire on the
Greek island of Spetses. It is a *cellular automaton*: a grid of squares
where each step, each square's next state depends on its neighbors. Their
model gives the chance that one burning square sets one of its neighbors
on fire during one step:

```text
chance = P_H * (1 + p_veg) * (1 + p_den)
```

* **`P_H` = 0.58** (in `science.py`) is the base chance for an average
  fuel: a little higher than a coin flip.
* **`p_veg`** adjusts for the *kind* of fuel. For instance, dry grass catches more easily
  (+0.4), longleaf pine is average (0.0), and damp hardwood litter resists
  (−0.4).
* **`p_den`** adjusts for *how much* fuel there is. The provided
  `science.density_factor(fuel)` turns a fuel load into `1 + p_den`.

For example, a pine square with fuel 0.8 has
`0.58 * (1 + 0.0) * density_factor(0.8)`, which is about 0.67: a 67%
chance to catch from each burning neighbor in each step. The plants
compute this in `plants.py`, and `Home.ignition_chance()` in `cover.py`
uses the same idea. This number is what each square's
`ignition_chance()` returns.

Fire spreads only to the four side neighbors of a burning square (north,
south, west, and east). The published model also uses diagonal neighbors;
we leave them out to keep the loops simple. Part 2 adds wind, slope, and
how dry the fuel is.

## Sources

Alexandridis et al. (2008), "A cellular automata model for forest fire
spread prediction: the case of the wildfire that swept through Spetses
Island in 1990," *Applied Mathematics and Computation* 204(1); USDA Forest
Service and US Geological Survey, LANDFIRE.
