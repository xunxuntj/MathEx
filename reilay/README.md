# Reilay obstacle corridor search

This directory contains exploratory code for the first long problem.

The model is rebuilt from the statement:

- The robot center is treated as a point.
- Every obstacle becomes a forbidden disk of radius `9`.
- Obstacle centers form a triangular lattice with spacing `20`.
- A turn card changes direction by at most `5` degrees.

The script searches for safe polylines through the corridor network.  It does
not prove global optimality.

## Main idea

The free space is not a single line.  It is a repeated corridor network between
equal forbidden disks.  The script samples two kinds of corridor-center points:

- gate points: midpoints between adjacent obstacle centers;
- pocket points: centers of the triangular gaps among three adjacent obstacles.

If the straight segment between two candidate points keeps distance at least
`9` from every obstacle in the first `n` layers, the script connects them.  It
then searches this visibility graph for a path with the fewest `5`-degree turn
cards.

## Run

From this directory:

```bash
python3 corridor_search.py --max-n 8 --out corridor_results.json --svg-n 3
```

To allow bends inside the corridor, add grid samples:

```bash
python3 corridor_search.py --max-n 3 --grid-step 2.0 --out corridor_results_grid.json --svg-n 2
```

Outputs:

- `corridor_results.json`: path, card count, total turn, length, and clearance.
- `corridor_results.n3.svg`: optional drawing for the selected layer.

## Interpretation

The result is a candidate upper bound:

```text
M(n) <= reported card count
```

It is not a lower bound.  To prove optimality, one would still need a complete
argument excluding all paths with fewer cards, including continuous choices of
turn positions and turn angles.

## Draw corridor layers

To draw the repeated safe-corridor geometry for 9 layers:

```bash
python3 draw_layers.py --layers 9 --out layers9_corridors.svg --html layers9_corridors.html
```

The drawing marks:

- radius-9 forbidden disks;
- layer hexagon boundaries;
- two-circle gate centers;
- three-circle pocket centers;
- the corridor skeleton connecting gates and pockets.

Open `layers9_corridors.html` in a browser for zoom and pan.  Corridor points
are labeled by layer, for example `1-1`, `1-2`, `2-1`, `2-2`, so later
discussion can refer to a specific gate or pocket directly.
