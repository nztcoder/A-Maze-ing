"""
Maze generation and pathfinding module

This module provides the core classes for creating, generating, and navigating
mazes. The Cell class represents individual maze cells with wall states, while
the Maze class orchestrates the full generation pipeline: grid creation,
embedding the '42' decorative pattern, DFS-based wall carving, and BFS-based
shortest-path computation
"""

import random
import math
from collections import deque
import time
from typing import Optional


# def time_slower(seconds: int | float):
#     def decorator(func: Callable):
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             sleep(seconds)
#             result = func(*args, **kwargs)
#             return result
#         return wrapper
#     return decorator


class Cell():
    """Represents a single cell in the maze grid.

    Each cell has four walls (north, east, south, west) that can be either
    closed (True) or open (False), a position in the grid, and several state
    flags used during generation and pathfinding. Cells can also carry
    special markers like ' S' for start, ' E' for exit, or '42' for the
    decorative pattern.

    Attributes:
        n: Boolean state of the north wall. True means wall is closed.
        e: Boolean state of the east wall. True means wall is closed.
        s: Boolean state of the south wall. True means wall is closed.
        w: Boolean state of the west wall. True means wall is closed.
        position: Tuple (x, y) with the cell's coordinates in the grid.
        special: String marker shown in the cell's center during rendering.
        visited: True if generation algorithm has processed this cell.
        path: True if this cell is part of the shortest path.
        seed: Reserved flag for seed-related marking (currently unused).
    """
    def __init__(
            self,
            n: bool, e: bool, s: bool, w: bool, position: tuple[int, int],
            special: str, visited: bool
            ) -> None:
        """Initialize a cell with walls, position, and state.

        Args:
            n: Initial state of the north wall (True = closed).
            e: Initial state of the east wall (True = closed).
            s: Initial state of the south wall (True = closed).
            w: Initial state of the west wall (True = closed).
            position: Tuple of (x, y) coordinates for this cell.
            special: String marker to display in the cell's center.
            visited: Initial visited state for the generation algorithm.
        """
        self.n = n
        self.e = e
        self.s = s
        self.w = w
        self.special = special
        self.seed: bool = False
        self.position = position
        self.visited = visited
        self.path: bool = False
        self.parent: Cell | None = None
        self.dead: bool = False

    def wall(
            self,
            wall: bool,
            # side: str,
            is_path: bool = False,
            is_42: bool = False
            ) -> str:
        """
        Return the colored 2-char string for one wall or corridor segment.

        Yellow square when is_42, black '██' when the wall is closed, blue
        square when the cell is on the path and the wall is open, white
        corridor '  ' otherwise.
        """

        blue_square = "\033[34m██\033[0m"
        white_corridor = "\033[47m  \033[0m"
        yellow_square = "\033[33m██\033[0m"

        if is_42:
            return yellow_square

        if not wall:
            if is_path:
                return blue_square
            if is_42:
                return yellow_square
            return white_corridor
        return "██"

    def representation(
            self, show_path: bool = False, neigh_path: Optional[dict] = None,
            neigh_42: Optional[dict] = None) -> list:
        """Return the 3x3 string matrix representing the cell for printing.

        The cell is rendered as a 3-row by 3-column grid of strings. Corners
        are always walls ('██'), edges show walls or open gaps based on the
        cell's wall state, and the center shows the special marker, the path
        indicator '··', or empty space depending on state.

        Returns:
            A list of 3 lists, each containing 3 strings. The outer list
            represents rows (top, middle, bottom), the inner lists represent
            columns (left, center, right) within each row.
        """
        if neigh_path is None:
            neigh_path = {"N": False, "E": False, "S": False, "W": False}

        if neigh_42 is None:
            neigh_42 = {"N": False, "E": False, "S": False, "W": False}

        blue_square = "\033[34m██\033[0m"
        white_corridor = "\033[47m  \033[0m"

        if "S" in self.special:
            center = "\033[92;47m██\033[0m"
        elif "E" in self.special:
            center = "\033[91;47m██\033[0m"
        elif show_path and self.path and "\033[" not in self.special:
            center = blue_square
        elif self.special == "  " or self.special == " P":
            center = white_corridor
        else:
            center = self.special

        w_char = "██"

        return [
            [
                w_char,
                self.wall(self.n, show_path and neigh_path["N"],
                          neigh_42["N"]), w_char
            ],
            [
                self.wall(
                    self.w, show_path and neigh_path["W"], neigh_42["W"]),
                center,
                self.wall(
                    self.e, show_path and neigh_path["E"], neigh_42["E"])
            ],
            [
                w_char, self.wall(self.s, show_path and neigh_path["S"],
                                  neigh_42["S"]), w_char
            ]
        ]

    def open_wall(self, wall: Optional[str]) -> None:
        """
        Set a specific wall to the open state.
        """
        if wall == "N":
            self.n = False
        if wall == "E":
            self.e = False
        if wall == "S":
            self.s = False
        if wall == "W":
            self.w = False

    def count_open_walls(self) -> int:
        i = 0
        if self.n is False:
            i += 1
        if self.e is False:
            i += 1
        if self.s is False:
            i += 1
        if self.w is False:
            i += 1
        return i


class Maze():
    """
    Represents a complete maze with generation, pathfinding, and rendering.

    The Maze class manages a 2D grid of Cell objects with an entry, exit,
    and decorative '42' pattern. It supports recursive backtracker DFS
    generation (both perfect and non-perfect variants), BFS-based shortest
    path computation, terminal-based rendering with optional coloring and
    path animation.

    Attributes:
        height: Number of rows in the maze grid.
        width: Number of columns in the maze grid.
        perfect: True for single-path mazes, False allows multiple paths.
        entry: Tuple (x, y) coordinates of the start cell.
        exit: Tuple (x, y) coordinates of the end cell.
        output_file: Filename where the maze will be serialized.
        seed: Random seed for reproducible generation, or None for random.
        grid: 2D list of Cell objects, indexed as grid[y][x].
        stack: Stack used during DFS generation.
        path_cells: Ordered list of cells forming the shortest path.
    """
    def __init__(
            self,
            height: int,
            width: int,
            perfect: bool,
            entry: tuple,
            exit: tuple,
            output_file: str,
            seed: int | None = None
            ):
        """Initialize a maze with given dimensions and configuration.

        The grid itself is not created here — call create_grid() afterwards.
        The random number generator is seeded immediately if seed is provided,
        ensuring reproducible generation.
        """
        self.height = height
        self.width = width
        self.perfect = perfect
        self.entry = entry
        self.exit = exit
        self.output_file = output_file
        self.seed = seed
        self.grid: list[list[Cell]] = []
        random.seed(seed)
        self.stack: list[Cell] = []
        self.path_cells: list[Cell] = []

    def create_grid(self) -> None:
        """Build the initial grid of cells with all walls closed.

        Creates a height-by-width 2D grid of Cell objects. All walls are
        initially set to closed (True). The entry cell is marked with ' S',
        the exit with ' E', and other cells with empty ' '. The entry cell
        is pre-marked as visited so generation starts from there.
        """
        x1, y1 = self.entry
        x2, y2 = self.exit
        i = 0
        while i < self.height:
            j = 0
            row = []
            while j < self.width:
                if (j, i) == self.entry:
                    cell = Cell(True, True, True, True, (j, i), " S", True)
                elif (j, i) == self.exit:
                    cell = Cell(True, True, True, True, (j, i), " E", False)
                else:
                    cell = Cell(True, True, True, True, (j, i), "  ", False)
                row.append(cell)
                j += 1
            self.grid.append(row)
            i += 1

    def print_grid(
            self, show_path: bool = False, color: str = "\033[0m") -> None:
        """Print the maze to the terminal as an ASCII rendering.

        Each cell is rendered as a 3x3 block of characters. Walls are shown
        as solid blocks '██' and are colored with the given ANSI color code.
        Open passages are rendered as spaces. The center of each cell may
        show a special marker (S, E, 42) or the path indicator '··' if
        show_path is True and the cell is on the shortest path.

        show_path: If True, cells marked as part of the path are
            rendered with '··' in their center.
        color: ANSI escape sequence for coloring wall segments.
        """
        # blue path
        def is_p(c: Cell) -> bool:
            return c.path or c.special == " S" or c.special == " E"

        # 42 logic
        def is_42(c: Cell) -> bool:
            return c.special == "42" or "\033[33m" in c.special

        for y, row in enumerate(self.grid):
            i = 0
            while i < 3:
                for x, cell in enumerate(row):
                    neighs_path = {
                        "N": (y > 0 and is_p(self.grid[y-1][x])
                              and is_p(cell)),
                        "S": (y < self.height-1 and is_p(self.grid[y+1][x])
                              and is_p(cell)),
                        "E": (x < self.width-1 and is_p(self.grid[y][x+1])
                              and is_p(cell)),
                        "W": (x > 0 and is_p(self.grid[y][x-1])
                              and is_p(cell))
                    }

                    neighs_42 = {
                        "N": (y > 0 and is_42(self.grid[y-1][x])
                              and is_42(cell)),
                        "S": (y < self.height-1 and is_42(self.grid[y+1][x])
                              and is_42(cell)),
                        "E": (x < self.width-1 and is_42(self.grid[y][x+1])
                              and is_42(cell)),
                        "W": (x > 0 and is_42(self.grid[y][x-1])
                              and is_42(cell))
                    }

                    rep = cell.representation(
                        show_path=show_path,
                        neigh_path=neighs_path,
                        neigh_42=neighs_42
                        )

                    k = 0
                    while k < 3:
                        part = rep[i][k]
                        # paint only black walls dont touch color blocks
                        if part == "██" and "\033[" not in part:
                            print(color + part + "\033[0m", end="")
                        else:
                            print(part, end="")
                        k += 1
                print()
                i += 1

    @staticmethod
    def ft() -> list:
        """Create the decorative '42' pattern as a 2D list of cells.

        Returns a 5-row by 7-column grid where cells marked '42' are fully
        closed (part of the visible pattern) and cells marked ' ' are normal.
        This pattern is later embedded into the main grid by insert_forty2.
        """
        pre_ft = [
            [1, 0, 1, 0, 1, 1, 1],
            [1, 0, 1, 0, 0, 0, 1],
            [1, 1, 1, 0, 1, 1, 1],
            [0, 0, 1, 0, 1, 0, 0],
            [0, 0, 1, 0, 1, 1, 1]
        ]
        result = []
        y = 0
        for row in pre_ft:
            x = 0
            r_row = []
            for tp in row:
                if tp == 1:
                    cell = Cell(
                        True, True, True, True, (0, 0), "42", True)
                if tp == 0:
                    cell = Cell(
                        True, True, True, True, (0, 0), "  ", False)
                cell.position = (x, y)
                r_row.append(cell)
                x += 1
            result.append(r_row)
            y += 1
        return result

    def insert_forty2(self, ft: list[list[Cell]]) -> None:
        """Embed the '42' pattern into the center of the maze grid.

        Replaces cells in the center of the main grid with the '42' pattern
        cells returned by ft(). If the entry or exit coordinates fall on a
        closed '42' cell, raises an exception because the pattern would
        isolate the start or end.
        """
        c_x = int((self.width - 1) / 2) - 3
        c_y = int((self.height - 1) / 2) - 2
        j = 0
        while j < len(ft):
            i = 0
            while i < len(ft[j]):
                if ((c_x + i, c_y + j) == self.entry or
                        (c_x + i, c_y + j) == self.exit):
                    if ft[j][i].visited is True:
                        raise Exception(
                            "Error: Entry and Exit must be appart from 42 logo"
                            )
                self.grid[c_y + j][c_x + i] = ft[j][i]
                self.grid[c_y + j][c_x + i].position = (c_x + i, c_y + j)
                i += 1
            j += 1

    @staticmethod
    def remove_walls_in_between(
            current_cell: Cell, direction: str, next_cell: Cell
            ) -> None:
        """Open the walls between two adjacent cells in a given direction.

        Modifies both cells to reflect that they are now connected. The wall
        on current_cell's given direction is opened, and the opposite wall
        on next_cell is also opened, keeping the maze data consistent.
        """
        opposite_dir = {
            "N": "S",
            "S": "N",
            "E": "W",
            "W": "E"
        }
        current_cell.open_wall(direction)
        o_d = opposite_dir[direction]
        next_cell.open_wall(o_d)

    def get_neighbours(self, cell: Cell) -> dict:
        """Find all unvisited neighbors of a cell.

        Checks all four cardinal directions and returns neighbors that are
        within grid bounds and have not yet been visited by the generation
        algorithm.
        """
        x, y = cell.position
        result = {}
        # checing from 4 sides
        if x - 1 >= 0:
            if self.grid[y][x - 1].visited is False:
                result.update({"W": self.grid[y][x - 1]})
        if x + 1 < self.width:
            if self.grid[y][x + 1].visited is False:
                result.update({"E": self.grid[y][x + 1]})
        if y - 1 >= 0:
            if self.grid[y - 1][x].visited is False:
                result.update({"N": self.grid[y - 1][x]})
        if y + 1 < self.height:
            if self.grid[y + 1][x].visited is False:
                result.update({"S": self.grid[y + 1][x]})
        return result

    def get_visited_neighbours(self, cell: Cell) -> dict:
        """
        Find visited neighbours that are already connected to this cell.

        Returns only neighbours whose side facing `cell` is already open
        — i.e. there is an existing passage between them. This is used
        during path-building stages when you want to walk through the
        carved part of the maze rather than start digging new passages.
        """
        x, y = cell.position
        result = {}
        # checing from 4 sides
        if x - 1 >= 0:
            if self.grid[y][x - 1].visited is True:
                if self.grid[y][x - 1].e is False:
                    result.update({"W": self.grid[y][x - 1]})
        if x + 1 < self.width:
            if self.grid[y][x + 1].visited is True:
                if self.grid[y][x + 1].w is False:
                    result.update({"E": self.grid[y][x + 1]})
        if y - 1 >= 0:
            if self.grid[y - 1][x].visited is True:
                if self.grid[y - 1][x].s is False:
                    result.update({"N": self.grid[y - 1][x]})
        if y + 1 < self.height:
            if self.grid[y + 1][x].visited is True:
                if self.grid[y + 1][x].n is False:
                    result.update({"S": self.grid[y + 1][x]})
        return result

    def stage2(self) -> None:
        while self.stack:
            current = self.stack.pop(-1)
            neighbours = self.get_neighbours(current)
            if len(neighbours) > 0:
                self.dig_into_depth(current)

    def dig_into_depth(self, next_cell: Cell) -> None:
        current = None
        while True:
            # if current is None:
            current = next_cell
            neighbours = self.get_neighbours(current)
            if len(neighbours) > 0:
                direction, next_cell = random.choice(
                     list(neighbours.items()))
                Maze.remove_walls_in_between(
                    current, direction, next_cell)
                current.visited = True
                neighbours.pop(direction)
                if len(neighbours) > 0:
                    self.stack.append(current)
            else:
                current.visited = True
                break

    def stage3(self) -> None:
        for row in reversed(self.grid):
            for cell in reversed(row):
                if cell.visited is True and cell.special != "42":
                    neighbours = self.get_neighbours(cell)
                    if len(neighbours) > 0:
                        direction, next_cell = random.choice(
                            list(neighbours.items()))
                        Maze.remove_walls_in_between(
                            cell, direction, next_cell)
                        next_cell.visited = True
                        self.dig_into_depth(next_cell)

    # for the dead end
    def get_neighbours_of_the_dead_end(self, cell: Cell) -> dict:
        x, y = cell.position
        result = {}
        # checing from 4 sides
        if x - 1 >= 0:
            nb = self.grid[y][x - 1]
            if nb.special in [" P", "  ", " S", " F"]:
                result.update({"W": nb})
        if x + 1 < self.width:
            nb = self.grid[y][x + 1]
            if nb.special == "  " or nb.special == " P":
                result.update({"E": nb})
        if y - 1 >= 0:
            nb = self.grid[y - 1][x]
            if nb.special in [" P", "  ", " S", " F"]:
                result.update({"N": nb})
        if y + 1 < self.height:
            nb = self.grid[y + 1][x]
            if nb.special == "  " or nb.special == " P":
                result.update({"S": nb})
        return result

    def dead_end_open(self) -> None:
        to_choose = []
        for row in self.grid:
            for cell in row:
                if cell.dead is True or cell.count_open_walls() == 1:
                    if cell.special not in (" S", " E", "42"):
                        to_choose.append(cell)
        i = 0
        while True:
            if len(to_choose) > 0:
                his_choice = random.choice(to_choose)
                neighbours = self.get_neighbours_of_the_dead_end(his_choice)
                if len(neighbours) > 0:
                    direction, next_cell = random.choice(
                        list(neighbours.items()))
                    Maze.remove_walls_in_between(
                        his_choice, direction, next_cell)
                    to_choose.remove(his_choice)
                    i += 1
                else:
                    to_choose.remove(his_choice)
            else:
                break

    def stage1(self) -> None:
        start = self.grid[self.entry[1]][self.entry[0]]
        current = start
        next_cell: Optional[Cell] = None
        while True:
            if next_cell:
                current = next_cell
                next_cell = None
            neighbours = self.get_neighbours(current)
            if len(neighbours) > 0:
                # direction = None
                for dir, cell in list(neighbours.items()):
                    if cell.special == " E":
                        next_cell = cell
                        direction = dir
                        break
                if not next_cell:
                    direction, next_cell = random.choice(
                        list(neighbours.items()))
                Maze.remove_walls_in_between(current, direction, next_cell)
                current.visited = True
                next_cell.parent = current
                if next_cell.special == " E":
                    self.stack.append(current)
                    next_cell.visited = True
                    break
                neighbours.pop(direction)
                if len(neighbours) >= 0:
                    self.stack.append(current)
            elif len(self.stack) != 0:
                cell.dead = True
                next_cell = self.stack.pop(-1)
                current.visited = True
            else:
                current.visited = True
                break
        if self.stack:
            # self.stack[-1].special = " P"
            self.stack[-1].path = True

    # MazeGen actually. my alco algo
    def maze_gen(self) -> None:
        """Generate the maze by carving passages through the closed grid.

        Orchestrates the full generation pipeline: the initial DFS-based
        wall carving (stage1),
        connecting disconnected regions (build_the_path),
        and finalization stages. The result is a fully
        connected maze where every cell is reachable from the entry.
        """
        self.stage1()
        self.build_the_path()
        self.stage2()
        # self.stage3()
        if self.perfect is False:
            self.dead_end_open()
            # self.bfs()
            self.find_shortest_path()
        # all cells.path = False
        # starting from the start. checking parents
        # if there are two options to go, create a new stack of cells
        #
        # write_into_file(
        #     self.grid, self.output_file, self.entry, self.exit. self.path)

    # BFS
    # def pathfind(self):
    #     def get_neighbours(cell: Cell) -> list:
    #         x, y = cell.position
    #         result = []
    #         # checing from 4 sides
    #         if x - 1 >= 0:
    #             # if self.grid[y][x - 1].visited is True:
    #             if self.grid[y][x - 1].e is False:
    #                 result.append(self.grid[y][x - 1])
    #         if x + 1 < self.width:
    #             # if self.grid[y][x + 1].visited is True:
    #             if self.grid[y][x + 1].w is False:
    #                 result.append(self.grid[y][x + 1])
    #         if y - 1 >= 0:
    #             # if self.grid[y - 1][x].visited is True:
    #             if self.grid[y - 1][x].s is False:
    #                 result.append(self.grid[y - 1][x])
    #         if y + 1 < self.height:
    #             # if self.grid[y + 1][x].visited is True:
    #             if self.grid[y + 1][x].n is False:
    #                 result.append(self.grid[y + 1][x])
    #         return result

    #     current = None
    #     visited = set()
    #     neighbours = []
    #     queue = deque()
    #     # gstack = []
    #     while self.grid[self.exit[1]][self.exit[0]] not in neighbours:
    #         if not current:
    #             current = start
    #         neighbours = get_neighbours(current)
    #         for cell in neighbours:
    #             visited.add(cell)

        # gstack.append(start)
        # get neighbours with open walls
        # if there are more then one we need to start dig in more directions
        # how?

    def bfs(self) -> None:
        def get_neighbours(cell: Cell) -> list[Cell]:
            x, y = cell.position
            result = []
            # checing from 4 sides
            if x - 1 >= 0:
                # if self.grid[y][x - 1].visited is True:
                if self.grid[y][x - 1].e is False:
                    result.append(self.grid[y][x - 1])
            if x + 1 < self.width:
                # if self.grid[y][x + 1].visited is True:
                if self.grid[y][x + 1].w is False:
                    result.append(self.grid[y][x + 1])
            if y - 1 >= 0:
                # if self.grid[y - 1][x].visited is True:
                if self.grid[y - 1][x].s is False:
                    result.append(self.grid[y - 1][x])
            if y + 1 < self.height:
                # if self.grid[y + 1][x].visited is True:
                if self.grid[y + 1][x].n is False:
                    result.append(self.grid[y + 1][x])
            return result

        start: Cell = self.grid[self.entry[1]][self.entry[0]]
        path = [start]
        queue = deque([(start, path)])
        visited = set()
        visited.add(start)

        while queue:
            # print("q")
            current, path = queue.popleft()
            # print(current.special)
            if current.position == self.exit:
                # return path
                break
            nbs = get_neighbours(current)
            for n in nbs:
                if n not in visited:
                    visited.add(n)
                    queue.append((n, path + [n]))
        for r in self.grid:
            for cell in r:
                cell.path = False
        for cell in path:
            x, y = cell.position
            self.grid[y][x].path = True
            if self.grid[y][x].special not in [" S", " E", "42"]:
                self.grid[y][x].special = " P"

    @staticmethod
    def distance(point_a: tuple[int, int], point_b: tuple[int, int]) -> float:
        x1, y1 = point_a
        x2, y2 = point_b
        return math.sqrt(((x2 - x1)**2 + (y2 - y1)**2))

    # using the stack after the first stage
    # we have a path, but there is a possibilty of gaps
    # so i need to track them
    def build_the_path(self) -> None:
        """Ensure continuity of the path accumulated in the generation stack.

        Iterates through consecutive cells in the stack produced by the DFS
        generation. When two neighboring stack entries are not adjacent in
        the grid (a gap), digs additional passages to bridge them. Marks
        all bridged cells with path = True and special = ' P' for later
        rendering.
        """
        i = 0
        next_cell: Cell | None = None
        while i < len(self.stack) - 1:
            if not next_cell:
                cell = self.stack[i]
            next_stack_cell = self.stack[i + 1]
            a = cell.position
            b = next_stack_cell.position
            if abs(b[0] - a[0]) + abs(b[1] - a[1]) == 1:
                if cell.position != self.entry:
                    cell.special = " P"
                next_cell = None
            else:
                vertical_d = next_stack_cell.position[1] - cell.position[1]
                horisontal_d = next_stack_cell.position[0] - cell.position[0]
                if abs(vertical_d) > abs(horisontal_d):
                    if vertical_d > 0:
                        directon_for_dig = "S"
                    else:
                        directon_for_dig = "N"
                else:
                    if horisontal_d > 0:
                        directon_for_dig = "E"
                    else:
                        directon_for_dig = "W"
                neighbours = self.get_visited_neighbours(cell)
                next_cell = neighbours.get(directon_for_dig)
            if cell.special != " S":
                cell.special = " P"
            cell.path = True
            i += 1
        self.stack[-1].path = True
        neighbours = self.get_visited_neighbours(self.stack[-1])
        for next_cell in neighbours.values():
            if next_cell.special == " E":
                next_cell.path = True
        # if len(self.stack) > 0:
        #     last = self.stack[-1]

    # DFS algo
    def find_shortest_path(self) -> None:
        """
        Compute the shortest path from entry to exit using BFS

        Resets all cells' path flags, then performs a breadth-first search
        starting from the entry cell. Traversal follows open passages only
        (where walls between cells are absent). Once the exit is reached,
        the path is reconstructed by walking back through recorded parent
        pointers

        After completion, cells on the shortest path have path = True, and
        self.path_cells contains them in order from entry to exit
        """
        for row in self.grid:
            for cell in row:
                cell.path = False

        start_x, start_y = self.entry
        end_x, end_y = self.exit
        start = self.grid[start_y][start_x]
        end = self.grid[end_y][end_x]

        queue = [start]
        came_from = {start: None}

        while len(queue) > 0:
            current = queue.pop(0)

            if current == end:
                break

            x, y = current.position

            if not current.n and y - 1 >= 0:
                neighbour = self.grid[y - 1][x]
                if neighbour not in came_from:
                    came_from[neighbour] = current
                    queue.append(neighbour)

            if not current.e and x + 1 < self.width:
                neighbour = self.grid[y][x + 1]
                if neighbour not in came_from:
                    came_from[neighbour] = current
                    queue.append(neighbour)

            if not current.s and y + 1 < self.height:
                neighbour = self.grid[y + 1][x]
                if neighbour not in came_from:
                    came_from[neighbour] = current
                    queue.append(neighbour)

            if not current.w and x - 1 >= 0:
                neighbour = self.grid[y][x - 1]
                if neighbour not in came_from:
                    came_from[neighbour] = current
                    queue.append(neighbour)

        self.path_cells = []
        current = end
        while current is not None:
            current.path = True
            self.path_cells.append(current)
            current = came_from.get(current)

        self.path_cells.reverse()

    def animate_path(self, color: str = "\033[0m") -> None:
        """
        Animate the drawing of the shortest path cell by cell

        Clears all path flags, then incrementally re-enables them one cell
        at a time in the order from entry to exit, redrawing the full maze
        after each step with a small delay. The animation ends with the
        complete path visible
        """
        for cell in self.path_cells:
            cell.path = False

        print("\033[H\033[J", end="")
        self.print_grid(True, color)
        time.sleep(0.3)

        for cell in self.path_cells:
            cell.path = True
            print("\033[H\033[J", end="")
            self.print_grid(True, color)
            time.sleep(0.1)
