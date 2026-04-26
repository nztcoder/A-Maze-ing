"""
A-Maze-ing entry point: CLI, file output, and interactive menu glue.

This module wires the parser, the Maze generator, and the terminal UI
together. It also handles encoding the maze into the hex-per-cell
format written to the output file.
"""

import sys
from mazegen import Maze, parsing, InputCheck, ParsingError, write_into_file
import random
from pydantic import ValidationError


def run_menu(my_maze: Maze, message: str) -> None:
    """
    Launch the interactive terminal menu for the maze

    Presents a looping menu with options to regenerate the maze, toggle
    shortest-path display, animate the path, cycle through wall colors,
    and quit. Redraws the maze after each action to reflect changes
    """
    show_path = False
    # black, red, green, purple, cyan, dark gray, bright cyan
    colors = [
        "\033[30m",
        "\033[31m",
        "\033[32m",
        "\033[0;35m",
        "\033[36m",
        "\033[90m",
        "\033[96m"
        ]
    color_index = 0

    yellow_square = "\033[33m██\033[0m"
    for row in my_maze.grid:
        for cell in row:
            if cell.special == "42":
                cell.special = yellow_square

    while True:
        # Escape sequence to clean terminal screen
        print("\033[H\033[J", end="")
        if message != "":
            print(message)
        x, y = my_maze.entry
        x1, y1 = my_maze.exit
        my_maze.grid[y][x].path = True
        my_maze.grid[y1][x1].path = True

        my_maze.print_grid(show_path, colors[color_index])

        print("\n=== A-Maze-ing ===")
        print("1. Regenerate maze")
        print("2. Show/Hide path")
        print("3. Animate path")
        print("4. Rotate colors")
        print("5. Quit")

        choice = input("Choice? (1-5): ")
        if choice == "1":
            my_maze.grid = []
            my_maze.stack = []
            random.seed(my_maze.seed)
            my_maze.create_grid()
            if my_maze.height > 6 and my_maze.width > 8:
                my_maze.insert_forty2(my_maze.ft())
            my_maze.maze_gen()
            my_maze.find_shortest_path()

            for row in my_maze.grid:
                for cell in row:
                    if cell.special == "42":
                        cell.special = yellow_square

        elif choice == "2":
            show_path = not show_path
        elif choice == "3":
            my_maze.animate_path(colors[color_index])
            show_path = True
        elif choice == "4":
            color_index = (color_index + 1) % len(colors)
        elif choice == "5" or choice == "q":
            break


def main() -> None:
    """
    Program entry point: parse arguments, generate maze, launch menu

    Expects exactly one command-line argument — the path to a
    configuration file. If the argument is missing or invalid, prints
    an error message and exits. Otherwise, parses the config, builds
    the maze through the full pipeline (create, embed '42', generate
    passages, compute path), writes it to the output file, and starts
    the interactive menu
    """
    message = ""
    if len(sys.argv) == 2:
        # it can be any file
        try:
            # if sys.argv[1] == r"^.+\.txt$":
            with open(sys.argv[1], "r") as config_file:
                config_data = config_file.read()
            # try:
                data_4_maze = parsing(config_data)
                validated = InputCheck.model_validate(data_4_maze)
            # else:
            #     raise ParsingError(
            #         "We are expecting .txt file for maze configuration")
        except ParsingError as p:
            print(str(p))
            exit(1)
        except ValidationError as v:
            print("Parsing error: ", str(v.errors()[0]['msg']))
            exit(1)
        except Exception as e:
            print("Could not open the file: ", str(e))
            exit(1)
        try:
            my_maze = Maze(**validated.model_dump())
            my_maze.create_grid()
            if my_maze.width > 8 and my_maze.height > 6:
                my_maze.insert_forty2(my_maze.ft())
            else:
                message = "Due to the size, 42 logo was omitted"
            my_maze.maze_gen()
            write_into_file(my_maze)
            run_menu(my_maze, message)

        except Exception as e:
            print(str(e))
            exit(1)
    else:
        print("The Amazing reqiuers <config_file> as a given parameter")


if __name__ == "__main__":
    main()
