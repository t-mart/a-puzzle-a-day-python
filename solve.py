from __future__ import annotations

import json
import shutil
from collections.abc import Iterable
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import numpy.typing as npt
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

BoardArray = npt.NDArray[np.int_]

BOARD_DIM_SIZE = 7

# The starting board, with fake pieces that make the grid regular
# In the rest of this code, this board acts like any other piece.
START_BOARD = np.array(
    [
        [0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 1],
    ],
    np.int_,
)


def iter_orientations(piece: list[list[int]]) -> Iterable[BoardArray]:
    # here, we're trying to collect all the UNIQUE orientations of the piece, so
    # that we don't do any more work than we need to. in other words, take
    # advantage of symmetry
    base = np.array(piece, np.int_)
    orientations: list[BoardArray] = []

    # iterate through all the orientations. outer loop controls flipping the piece.
    # inner loop controls rotating it.
    for flipped in (base, np.fliplr(base)):
        for rotation in (np.rot90(flipped, k=k) for k in range(4)):
            # first, check if shapes are different. if different, it's a unique
            # orientation, so append it. (this also short-circuits out of checking
            # if different-shaped pieces are equal in next step, which is invalid.)
            # second, only if shapes are equal, check if arrays are different.
            # append if different.
            if all(
                rotation.shape != other.shape or not np.all(rotation == other)
                for other in orientations
            ):
                orientations.append(rotation)

    yield from orientations


def fits(
    *pieces: BoardArray,
) -> bool:
    return np.max(sum(pieces)) == 1


def iter_placements(
    oriented_piece: BoardArray,
) -> Iterable[BoardArray]:

    for top_row in range(0, BOARD_DIM_SIZE - oriented_piece.shape[0] + 1):
        for left_col in range(0, BOARD_DIM_SIZE - oriented_piece.shape[1] + 1):
            placement = np.zeros((7, 7), np.int_)
            placement[
                top_row : top_row + oriented_piece.shape[0],
                left_col : left_col + oriented_piece.shape[1],
            ] = oriented_piece
            if fits(START_BOARD, placement):
                yield placement


def iter_placed_orientations(piece: list[list[int]]) -> Iterable[BoardArray]:
    for orientation in iter_orientations(piece):
        for placement in iter_placements(orientation):
            yield placement


# Real pieces
RECT = list(
    iter_placed_orientations(
        [
            [1, 1, 1],
            [1, 1, 1],
        ]
    )
)
RECT_NOTCH_CORNER = list(
    iter_placed_orientations(
        [
            [1, 1, 1],
            [1, 1, 0],
        ]
    )
)
RIGHT = list(
    iter_placed_orientations(
        [
            [1, 1, 1],
            [1, 0, 0],
            [1, 0, 0],
        ]
    )
)
ESS = list(
    iter_placed_orientations(
        [
            [0, 1, 1],
            [0, 1, 0],
            [1, 1, 0],
        ]
    )
)
ELL = list(
    iter_placed_orientations(
        [
            [1, 1, 1, 1],
            [1, 0, 0, 0],
        ]
    )
)
SIGN_POST = list(
    iter_placed_orientations(
        [
            [0, 0, 1, 0],
            [1, 1, 1, 1],
        ]
    )
)
CRINKLE = list(
    iter_placed_orientations(
        [
            [0, 1, 1, 1],
            [1, 1, 0, 0],
        ]
    )
)
CEE = list(
    iter_placed_orientations(
        [
            [1, 1],
            [0, 1],
            [1, 1],
        ]
    )
)


PIECE_PLACEMENTS = [
    RECT,
    RECT_NOTCH_CORNER,
    RIGHT,
    ESS,
    ELL,
    SIGN_POST,
    CRINKLE,
    CEE,
]


def _solve(
    set_pieces: list[BoardArray],
    set_pieces_sum: BoardArray,
    pieces_left: list[list[BoardArray]],
) -> Iterable[list[BoardArray]]:
    if np.max(set_pieces_sum) > 1:
        return

    if len(pieces_left) == 0:
        yield set_pieces
    else:
        placements, pieces_left = pieces_left[0], pieces_left[1:]
        for placement in placements:
            yield from _solve(
                set_pieces=set_pieces + [placement],
                set_pieces_sum=set_pieces_sum + placement,
                pieces_left=pieces_left,
            )


def solve() -> Iterable[list[BoardArray]]:
    """Single process solver"""
    yield from _solve(
        set_pieces=[START_BOARD],
        set_pieces_sum=START_BOARD,
        pieces_left=PIECE_PLACEMENTS,
    )


def _solvetolist(
    args: tuple[list[BoardArray], BoardArray, list[list[BoardArray]]]
) -> list[list[BoardArray]]:
    # needed because generator object can't be passed between processes
    # also, we take args in as a single tuple, which lets it work with more of
    # multiprocessing.Pool's methods
    return list(_solve(args[0], args[1], args[2]))


def solvemp(progress: Progress, task_id: TaskID) -> Iterable[list[BoardArray]]:
    """Multiprocessing solver"""
    # this is the multiprocessing version of _solve
    # on it's own, solve() will produce every solution, but that takes a long time for a
    # single GIL-limited processor.
    # so instead, we choose to break up the work by feeding _solve arguments AS IF it
    # was some number of layers of recursion into it's work. This means bringing some of
    # _solve()'s logic up here, but it's not too hard.
    # with this work brought up, we can dispatch it out to different processors

    def arg_builder(layers: int):
        # generate arguments for _solve as if it was some number of layers of recursion
        # down
        assert 1 <= layers <= len(PIECE_PLACEMENTS)
        preset_pieces, pieces_for_mp = (
            PIECE_PLACEMENTS[:layers],
            PIECE_PLACEMENTS[layers:],
        )

        for partial_solution in _solve(
            set_pieces=[START_BOARD],
            set_pieces_sum=START_BOARD,
            pieces_left=preset_pieces,
        ):
            yield (partial_solution, sum(partial_solution), pieces_for_mp)

    layers = 2
    args = list(arg_builder(layers=layers))

    progress.update(task_id, total=len(args))

    with Pool() as pool:
        solution_subsets = pool.imap_unordered(_solvetolist, args, chunksize=128)
        for solution_subset in solution_subsets:
            for solution in solution_subset:
                yield solution
            progress.advance(task_id=task_id)


MONTH_DAY_DECODER = np.array(
    [
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "???"],
        ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "???"],
        ["001", "002", "003", "004", "005", "006", "007"],
        ["008", "009", "010", "011", "012", "013", "014"],
        ["015", "016", "017", "018", "019", "020", "021"],
        ["022", "023", "024", "025", "026", "027", "028"],
        ["029", "030", "031", "???", "???", "???", "???"],
    ]
)


if __name__ == "__main__":
    sln_root_dir = Path("./a-puzzle-a-day-solutions")

    if sln_root_dir.is_dir():
        shutil.rmtree(sln_root_dir)

    sln_root_dir.mkdir()

    with Progress(
        SpinnerColumn(),
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        "{task.completed}/{task.total}",
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("Solving...")
        for i, sln in enumerate(solvemp(progress, task), start=1):
            combined = sum(sln)

            name = "-".join(MONTH_DAY_DECODER[combined == 0])

            sln_path = sln_root_dir / f"{name}.json"

            if sln_path.exists():
                with sln_path.open("r") as sln_file:
                    data = json.load(sln_file)
            else:
                data = []

            # start board isn't necessary part of solution, so we look at sln[1:]
            # be careful: we assume the start board piece is always the 0th one, so if
            # the way the pieces are ordered in the solutions change, this will also
            # need to change
            data.append([piece.tolist() for piece in sln[1:]])

            with sln_path.open("w") as sln_file:
                json.dump(data, sln_file)

            # progress.console.print(
            #     f"Found solution for date {name} (#{len(data)} for this date, #{i} "
            #     "overall)"
            # )
