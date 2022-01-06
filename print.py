import json
import sys
from pathlib import Path

BOARD_DIM_SIZE = 7

solution_path = Path(sys.argv[1])
# solution_path = Path("./solutions/Nov-002.json")

with solution_path.open("r", encoding="utf-8") as solutions_file:
    solutions = json.load(solutions_file)

for i, solution in enumerate(solutions, start=1):
    print(f"Solution #{i}")
    for row_idx in range(BOARD_DIM_SIZE):
        line = "\t".join(
            "".join(("#" if col == 1 else ".") for col in piece[row_idx])
            for piece in solution
        )
        print(line)
    print()
