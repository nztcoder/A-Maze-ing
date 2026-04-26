"""
Configuration parsing and validation for A-Maze-ing.

Parses a plain-text config file into a dict of maze parameters and
validates types, ranges, and file-name patterns via a Pydantic model.
"""

from pydantic import BaseModel, model_validator, Field
from typing import Optional, TypeAlias, Self
# import sys
# import os

# terminal_width = os.get_terminal_size()
# print(terminal_width)


class ParsingError(Exception):
    """
    Raised when a config file line cannot be parsed or has an unknown key.
    """
    def __init__(self, message: str) -> None:
        self.message = message


ConfigValue: TypeAlias = Optional[int | bool | str | tuple[int, int]]


def parsing(data: str) -> dict[str, ConfigValue]:
    """
    Parse the raw text of a config file into a dict of maze parameters.

    Each non-empty, non-comment line must have the form KEY=VALUE.
    Recognised keys: WIDTH, HEIGHT, ENTRY, EXIT, OUTPUT_FILE, PERFECT, SEED.
    Keys are lowercased in the returned dict so they map directly onto the
    Maze / InputCheck constructors.

    ParsingError: If a line is malformed or contains an unknown key.
    """
    rows = data.split("\n")
    result: dict[str, ConfigValue] = {"seed": None}
    for row in rows:
        if row.startswith("#") or row == "":
            continue
        else:
            entry = row.split("=")
            if len(entry) == 2:
                if (
                        entry[0] == "WIDTH" or
                        entry[0] == "HEIGHT"
                        ):
                    result.update({entry[0].lower(): int(entry[1])})
                elif (
                        entry[0] == "ENTRY" or
                        entry[0] == "EXIT"
                        ):
                    ponit_pair = entry[1].split(",")
                    result.update(
                        {entry[0].lower(): (int(ponit_pair[0]),
                                            int(ponit_pair[1]))}
                        )
                elif entry[0] == "OUTPUT_FILE":
                    result.update({entry[0].lower(): entry[1]})
                elif entry[0] == "PERFECT":
                    if entry[1] == "True":
                        result.update({entry[0].lower(): True})
                    elif entry[1] == "False":
                        result.update({entry[0].lower(): False})
                elif entry[0] == "SEED":
                    result.update({entry[0].lower(): int(entry[1])})
                else:
                    raise ParsingError(f"Unknown parameter: {row}")
            else:
                raise ParsingError(f"ParsingError: {row} entry is invalid")

    return result


class InputCheck(BaseModel):
    """
    Pydantic schema that validates parsed config values.

    Ensures width/height are positive, the output file ends in '.txt',
    and seed, if given, is non-negative. Entry and exit ranges relative
    to the grid are not yet validated here.
    """
    width: int
    height: int
    entry: tuple[int, int]
    exit: tuple[int, int]
    # r is raw string, because regex uses a lot of backslashes
    # without r Python would treat those as escape char
    # ^ is start of the string, $ is the end
    # . is any char, + is one or more previous token
    # \. is literal
    output_file: str = Field(min_length=5, pattern=r"^.+\.txt$")
    perfect: bool
    seed: Optional[int] = Field(default=None, ge=0)

    # i can check if the entry and exit are in the grid
    @model_validator(mode="after")
    def validator(self) -> Self:
        if self.entry == self.exit:
            raise ValueError("Entry and Exit has to be different")
        if self.width < 1 or self.height < 1:
            raise ValueError("Size parameters have to be greater then ZERO")
        if (self.entry[0] < 0 or
                self.entry[1] < 0 or
                self.exit[0] < 0 or
                self.exit[1] < 0):
            raise ValueError(
                "Entry/Exit coordinates have to be positive integers"
                )
        # check start and entry
        if (self.entry[0] >= self.width or self.entry[1] >= self.height or
                self.entry[0] < 0 or self.entry[1] < 0):
            raise ValueError("Entry point is out of Maze bounds")
        if (self.exit[0] >= self.width or self.exit[1] >= self.height or
                self.entry[0] < 0 or self.entry[1] < 0):
            raise ValueError("Exit point is out of Maze bounds")
        # if self.width < 9 or self.height < 7:
        #     raise ValueError("Maze size is too small to",
        #                      "create a labirynth with '42' logo."
        #                      "\nMin size is 9 x 7")
        return self
