# Where the sketch table comes from

*Optional reading: you don't need any of this to do the assignment.*

## Tangible Landscape

At NC State University, researchers at the Center for Geospatial Analytics
built **Tangible Landscape**, a way to explore a landscape with your hands.
People shape a model of the land out of sand. A scanner above the table
reads the shape of the sand, a computer simulates what would happen there
(how water would flow, or how a fire would spread), and a projector paints
the results right back onto the sand.

To try out ideas, people place markers and felt shapes on the sand and draw
lines with a laser pointer: a new neighborhood here, a firebreak there.
Then they watch the simulation respond. Because everyone is gathered around
the same table, fire managers, planners, and neighbors can test "what if?"
questions together, without needing to know how the simulation code works.

## How Good Fire borrows from it

Your sketch table is a small, digital version of the same idea.

| Tangible Landscape | Good Fire |
| --- | --- |
| sculpting and scanning a sand model | the provided 30 x 30 map of hills, river, pines, and meadow |
| placing felt shapes to mark areas | sketching a `Polygon` (homes, a pond, a meadow) |
| drawing a line with a laser pointer | sketching a `Polyline` (a river, a road) |
| the projected fire simulation | the `Landscape` and its `step()` |
| saving a scenario to share or revisit | **Save sketch**, which writes each shape's `repr()` |
| scanning a physical model | **Sketch from photo**, which reads a marker drawing on paper |

In Part 2 you will place fire-management treatments (prescribed burns,
fuel breaks, and Firewise protection) as sketched shapes, the way Tangible
Landscape users place treatments on the sand, and test a plan against a
whole fire season.

## Read more

* Petrasova, A., Harmon, B., Petras, V., Tabrizian, P., and Mitasova, H.
  (2018). *Tangible Modeling with Open Source GIS*, 2nd ed. Springer. The
  chapter on wildfire spread describes the fire scenarios people test on
  the sand table.
