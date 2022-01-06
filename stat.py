# number of solutions
# most- and least-solveable days
# valid versus invalid solutions
from pathlib import Path
from typing import Optional
import json

VALID_MONTH_DAYS = {
    "Jan": 31,
    "Feb": 29,  # include leap day
    "Mar": 31,
    "Apr": 30,
    "May": 31,
    "Jun": 30,
    "Jul": 31,
    "Aug": 31,
    "Sep": 30,
    "Oct": 31,
    "Nov": 30,
    "Dec": 31,
}

sln_root_path = Path("./a-puzzle-a-day-solutions")

def is_valid_date(path: Path) -> bool:
    left, right = path.stem.split("-")
    try:
        intright = int(right)
    except ValueError:
        return False
    return left in VALID_MONTH_DAYS and intright <= VALID_MONTH_DAYS[left]


solution_count = 0
valid_solution_count = 0

most_solveable_count: Optional[int] = None
most_solvable_name: Optional[str] = None

least_solveable_count: Optional[int] = None
least_solvable_name: Optional[str] = None

for sln_path in sln_root_path.iterdir():
    with sln_path.open("r", encoding="utf-8") as sln_file:
        data = json.load(sln_file)

    sln_for_date = len(data)

    solution_count += sln_for_date

    if is_valid_date(sln_path):
        valid_solution_count += sln_for_date

        if most_solveable_count is None or sln_for_date > most_solveable_count:
            most_solveable_count = sln_for_date
            most_solvable_name = sln_path.stem

        if least_solveable_count is None or sln_for_date < least_solveable_count:
            least_solveable_count = sln_for_date
            least_solvable_name = sln_path.stem

print(f"{solution_count=}")
print(f"{valid_solution_count=}, {valid_solution_count*100/solution_count=:.2f}")

print(f"{most_solveable_count=}, {most_solvable_name=}")
print(f"{least_solveable_count=}, {least_solvable_name=}")
