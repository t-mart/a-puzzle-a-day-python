import json
import sys
from pathlib import Path
from rich.console import Console
from rich.text import Text

CONSOLE = Console()
BOARD_DIM_SIZE = 7
FILLED_SQUARE_CHAR = "█"
OPEN_SQUARE_CHAR = "░"

# these are from the D3 category 10
COLORS = [
    "#1f77b4",  # blue
    "#ff7f0e",  # orange
    "#2ca02c",  # green
    "#d62728",  # red
    "#9467bd",  # purple
    "#8c564b",  # brown
    "#e377c2",  # pink
    "#17becf",  # cyan
]

Piece = list[list[int]]
Solution = list[Piece]


def print_solution(solution: Solution) -> None:
    board: list[list[Text]] = []
    cols_in_rows = [6, 6, 7, 7, 7, 7, 3]
    for col_in_row in cols_in_rows:
        board.append([Text(OPEN_SQUARE_CHAR) for _ in range(col_in_row)])

    for color, piece in zip(COLORS, solution):
        for piece_row, board_row_idx in zip(piece, range(len(board))):
            for piece_col, board_col_idx in zip(
                piece_row, range(len(board[board_row_idx]))
            ):
                if piece_col == 0:
                    continue
                board[board_row_idx][board_col_idx] = Text(
                    FILLED_SQUARE_CHAR, style=color
                )

    for row in board:
        for col in row:
            CONSOLE.print(col, end='')
        CONSOLE.print()
    CONSOLE.print()


solution_path = Path(sys.argv[1])
# solution_path = Path("./a-puzzle-a-day-solutions/Oct-006.json")

with solution_path.open("r", encoding="utf-8") as solutions_file:
    solutions = json.load(solutions_file)

for i, solution in enumerate(solutions, start=1):
    print(f"Solution #{i}")
    print_solution(solution)
