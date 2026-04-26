from .maze import Maze, Cell


# Bit Direction
# 0 (LSB) North
# 1 East
# 2 South
# 3 West
def decode(cell: Cell) -> str:
    """
    Encode a cell's walls into a 4-bit binary string.

    Bit order (MSB -> LSB): West, South, East, North.
    Each bit is 1 if that wall is closed, 0 if open.
    The result is a 4-char string like '1011', later converted to hex
    and written to the maze output file.
    """
    result = ""
    north = int(cell.n)
    east = int(cell.e)
    south = int(cell.s)
    west = int(cell.w)
    result = str(west) + str(south) + str(east) + str(north)
    return result


def get_right_dir(cell: Cell, maze: Maze) -> tuple[str, Cell] | None:
    """
    Return the next step of the path from `cell`, or None if there is none.

    Inspects the four neighbours of `cell` and picks one that:
      - is on the shortest path (`path is True`),
      - is not the parent we came from,
      - is connected to `cell` through an open wall.

    Returns a ("N"|"E"|"S"|"W", Cell) tuple, or None when no such
    neighbour exists (e.g. at the exit).
    """
    x, y = cell.position
    # result = ()
    # checing from 4 sides
    if x - 1 >= 0:
        if (maze.grid[y][x - 1].path is True and
                cell.parent != maze.grid[y][x - 1]):
            if maze.grid[y][x - 1].e is False and cell.w is False:
                return ("W", maze.grid[y][x - 1])
    if x + 1 < maze.width:
        if (maze.grid[y][x + 1].path is True and
                cell.parent != maze.grid[y][x + 1]):
            if maze.grid[y][x + 1].w is False and cell.e is False:
                return ("E", maze.grid[y][x + 1])
    if y - 1 >= 0:
        if (maze.grid[y - 1][x].path is True and
                cell.parent != maze.grid[y - 1][x]):
            if maze.grid[y - 1][x].s is False and cell.n is False:
                return ("N", maze.grid[y - 1][x])
    if y + 1 < maze.height:
        if (maze.grid[y + 1][x].path is True and
                cell.parent != maze.grid[y + 1][x]):
            if maze.grid[y + 1][x].n is False and cell.s is False:
                return ("S", maze.grid[y + 1][x])
    return None


def get_directions(maze: Maze) -> str:
    """
    Walk the shortest path from entry to exit and return the moves.

    Starting at the entry cell, repeatedly asks get_right_dir for the
    next step, concatenating one letter per move ('N', 'E', 'S', 'W').
    Stops when the exit cell is reached. The result is the string
    appended to the output file as the solution trail.
    """
    current = maze.grid[maze.entry[1]][maze.entry[0]]
    result = ""
    # next_cell: Optional[Cell] = None
    while True:
        right_dir = get_right_dir(current, maze)
        if right_dir:
            dir, next_cell = right_dir
        result += dir
        next_cell.parent = current
        current = next_cell
        if next_cell.special == " E":
            break
    return result


def write_into_file(maze: Maze) -> None:
    """
    Serialise the maze to the configured output file.

    Layout:
        - grid: one line per row, each cell encoded as a single hex
          digit whose 4 bits describe the wall state (see decode).
        - blank line.
        - entry coordinates as "x, y".
        - exit coordinates as "x, y".
        - solution string from get_directions (e.g. "EENNSS").
    """
    result = ""
    for row in maze.grid:
        for cell in row:
            string = decode(cell)

            to_add = str(hex(int(string, base=2)))

            result += to_add.removeprefix("0x").capitalize()
        result += "\n"
    result += "\n"
    entry = str(maze.entry).removeprefix("(")
    result += entry.removesuffix(")") + "\n"
    finish = str(maze.exit).removeprefix("(")
    result += finish.removesuffix(")") + "\n"
    result += get_directions(maze)
    try:
        with open(maze.output_file, mode="w") as f:
            f.write(result)
    except Exception:
        raise Exception
