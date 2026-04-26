*This project has been created as part of the 42 curriculum by vsudak, oznachki.*

# A-Maze-ing

## Description

A-Maze-ing is a Python-based maze generator and visualizer that produces randomized
mazes from a configuration file. The program generates a maze, finds the shortest path
from entry to exit, saves the result to a file in hexadecimal wall-encoding format, and
provides an interactive terminal-based visualization.

Each cell has up to four walls (north, east, south, west) encoded as a hexadecimal
digit. The generator supports both perfect mazes (exactly one path between entry and
exit) and non-perfect mazes (with loops). A hidden "42" pattern is embedded into
every maze as decorative feature built from fully closed cells.

Key features include configurable maze dimensions, reproducible generation via seed,
BFS-based shortest path computation, interactive menu with live wall color rotation,
animated path drawing, and an importable `mazegen` package for reuse in other projects.

## Instructions

### Prerequisites
- Python 3.11 or later
- `pip` package manager

### Installation

Install project dependencies:

```bash
make install
```

### Running

Execute the main program with a configuration file as argument:

```bash
virt_env/bin/python3 a_maze_ing.py config.txt
```

Or using Make:

```bash
make run
```

The configuration file can have any name — `config.txt` is just the default example
provided in the repository.

### Debug Mode

Run under Python debugger (pdb):

```bash
make debug
```

### Cleaning Up

Remove temporary files and caches and virt_env/:

```bash
make clean
```

### Linting

Run flake8 and mypy checks:

```bash
make clean
make lint
```

## Configuration File Format

The configuration file uses `KEY=VALUE` pairs with one pair per line. Lines starting
with `#` are treated as comments and ignored.

### Mandatory Keys

| Key           | Description                          | Example              |
|---------------|--------------------------------------|----------------------|
| `WIDTH`       | Maze width in cells                  | `WIDTH=20`           |
| `HEIGHT`      | Maze height in cells                 | `HEIGHT=15`          |
| `ENTRY`       | Entry coordinates (x,y)              | `ENTRY=0,0`          |
| `EXIT`        | Exit coordinates (x,y)               | `EXIT=19,14`         |
| `OUTPUT_FILE` | Output filename for generated maze   | `OUTPUT_FILE=maze.txt` |
| `PERFECT`     | Whether maze is perfect (True/False) | `PERFECT=True`       |

### Optional Keys

| Key    | Description                                    | Example    |
|--------|------------------------------------------------|------------|
| `SEED` | Random seed for reproducible generation        | `SEED=42`  |

### Example Configuration
HEIGHT=15
WIDTH=15
PERFECT=False
ENTRY=0,0
EXIT=14,14
OUTPUT_FILE=maze.txt
SEED=19

## Output File Format

Each cell is encoded as one hexadecimal digit where bits indicate closed walls:

| Bit | Direction |
|-----|-----------|
| 0   | North     |
| 1   | East      |
| 2   | South     |
| 3   | West      |

A bit value of `1` means the wall is closed, `0` means open. For example, digit `A`
(binary `1010`) means east and west walls are closed, north and south are open.

The output file contains:
1. One line per maze row, with cells encoded as hex digits in sequence
2. An empty line separator
3. Entry coordinates in format `x,y`
4. Exit coordinates in format `x,y`
5. Shortest path as a sequence of direction letters (N, E, S, W)

## Maze Generation Algorithm

The algorithm was made by Valentyn and it is based on DFS algo,
implemented iteratively using an explicit stack for better memory
efficiency and to avoid Python recursion limits on large mazes.

### How it works

1. Start from the start cell (typically the entry cell) and mark it as visited
2. While there are cells in the stack:
   - Check the current cell's unvisited neighbors
   - If unvisited neighbors exist, choose one at random, remove the wall between
     current and chosen cell, mark chosen as visited, push current onto stack,
     continue from chosen cell
   - If no unvisited neighbors, pop the stack to backtrack to the previous cell
3. 1st stage terminates when it found an Exit
4. 2nd stage builds branches around build Path until it doesn`t fullfil entire grid 

### Why we chose this algorithm

Valentyn: I`ve done this accordingly to the explanations of other students(E. Kramer and I. Classen)
and materials from the web.

For non-perfect maze mode, additional passes introduce controlled loops by
occasionally removing walls between already-connected cells.

### Shortest Path Algorithm

After generation, the shortest path from entry to exit is computed using
**Breadth-First Search (BFS)**. BFS guarantees the shortest path in graphs with
unit edge weights, which is exactly our case — every step between adjacent cells
costs the same.

The BFS traversal uses a queue and a `came_from` dictionary to track parent
relationships. Once the exit is reached, the path is reconstructed by walking
backwards through parents, then reversed to produce the sequence from entry
to exit.

## Visual Representation

The program provides a terminal-based ASCII visualization with the following
interactive features:

1. **Regenerate maze** — Produces a new random maze with the same configuration
2. **Show/Hide path** — Toggles display of the shortest path from entry to exit
3. **Animate path** — Progressively draws the shortest path cell-by-cell with
   delay between frames
4. **Rotate colors** — Cycles through available wall colors (black, red, green,
   purple, cyan, dark gray, bright cyan)
5. **Quit** — Exits the program

The entry cell is marked with `S`, the exit with `E`, and the "42" pattern is
highlighted in yellow. When path display is enabled, cells along the shortest
path are shown with `··` markers.

## Reusable Code

The `mazegen` package is designed for reuse in other Python projects. It provides:

- `Maze` class — main maze generator with grid, path, and output management
- `Cell` class — individual cell with wall state and metadata
- `parsing` function — utility to parse configuration dictionaries
- `ParsingError` — custom exception for configuration errors

### Installation as a Dependency

To reuse the mazegen, you need to install a_maze_ing-0.1.0-py3-none-any.whl into your enviroment

```bash
python3 pip install -m a_maze_ing-0.1.0-py3-none-any.whl
```

then import mazegen into your code

### Basic Usage Example

```python
from mazegen import Maze

# Create a 10x10 maze with reproducible seed
maze = Maze(
    width=10,
    height=10,
    perfect=True,
    entry=(0, 0),
    exit=(9, 9),
    output_file="my_maze.txt",
    seed=42
)

# Generate the maze structure
maze.create_grid()
maze.insert_forty2(maze.ft())
maze.path_gen()

# Find and access shortest path
maze.find_shortest_path()
shortest_path = maze.path_cells  # list of Cell objects from entry to exit

# Access the grid directly
for row in maze.grid:
    for cell in row:
        # cell.n, cell.e, cell.s, cell.w — wall states (True = closed)
        # cell.path — True if cell is on shortest path
        # cell.position — (x, y) tuple
        pass
```

## Advanced Features

### Wall Color Customization

Seven color options are available via the "Rotate colors" menu entry. The current
color is applied to all wall segments during rendering.

### Animated Path Drawing

The "Animate path" option replays the shortest-path computation visually, revealing
cells one by one from entry to exit. Animation speed is configurable via the
`sleep` parameter in the `animate_path` method.

### Non-perfect Maze Generation

When `PERFECT=False` is set, the generator introduces controlled loops after the
initial DFS pass, creating multiple paths between some cells while respecting the
maximum corridor width constraint.

## Team and Project Management

### Roles

- **vsudak** — Configuration parsing, maze generation algorithm,
  `insert_forty2` pattern, file output encoding
- **oznachki** — Graphical interface, interactive menu system, path visualization,
  color rotation, animation, BFS shortest-path implementation


### Planning Evolution

We initially planned to implement the entire project in about 10 days, with
algorithm development taking priority. In practice, the interactive visualization
and user interface took more time than expected because of coordination needed
with the algorithm side — changes to the `Cell` class required updates in both
rendering and generation code. The pip packaging step, which we underestimated,
took an additional 5 days to set up correctly.

### What Worked Well

- Dividing work by subsystem (algorithm vs UI) allowed parallel development
- Using git branches for experimental features prevented destabilizing the main code
- The `Cell` class as a shared interface made it easy to decouple rendering from
  generation logic

### What Could Be Improved

- Earlier agreement on data format between algorithm and visualization would have
  reduced refactoring
- More thorough unit testing from the start would have caught edge cases sooner
- Debug print statements accumulated during development and required cleanup later

### Tools Used

- **Python >= 3.11** as the primary language
- **Git** for version control and collaboration
- **flake8** and **mypy** for static code analysis
- **pydantic** for configuration validation
- **VS Code**
- **AI assistants** for algorithm design guidance, code review, and
  debugging assistance (see Resources section for details)

## Resources

### Documentation

- [Python 3 Language Reference](https://docs.python.org/3/reference/)
- [PEP 257 — Docstring Conventions](https://peps.python.org/pep-0257/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [setuptools documentation](https://setuptools.pypa.io/)

### Algorithm References

- Jamis Buck's blog "Maze Generation: Algorithm Recap" —
  <https://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithm-recap.html>
- Wikipedia: Maze generation algorithm —
  <https://en.wikipedia.org/wiki/Maze_generation_algorithm>
- Wikipedia: Breadth-first search —
  <https://en.wikipedia.org/wiki/Breadth-first_search>
- Think Labyrinth! by Walter D. Pullen (classic maze theory resource)

### AI Usage Disclosure

This project used AI assistants in several ways during
development. We believe in transparent disclosure of AI tools as recommended by
the 42 curriculum AI Instructions.

**For which tasks AI was used:**
- Explaining algorithmic concepts (DFS, BFS, recursive backtracking) before
  implementation
- Guiding the structure of the BFS shortest-path method
- Debugging specific issues (e.g., scoping errors in the menu loop, color
  rendering problems after animation)
- Reviewing code style and suggesting improvements
- Readme file compilation
- Doc strings compilation

The AI was used as a learning and debugging aid, not as a replacement for
understanding. All team members can explain every line of code they committed.
