"""Maze/ship map generation utilities for autonomous exploration experiments."""

from __future__ import annotations

import random
from typing import Iterable, List, Tuple

BLOCKED = 0
OPEN = 1
Cell = Tuple[int, int]
Grid = List[List[int]]


def in_bounds(x: int, y: int, size: int) -> bool:
    return 0 <= x < size and 0 <= y < size


def cardinal_neighbors(x: int, y: int, size: int) -> Iterable[Cell]:
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nx, ny = x + dx, y + dy
        if in_bounds(nx, ny, size):
            yield nx, ny


def surrounding_cells(x: int, y: int, size: int) -> Iterable[Cell]:
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if in_bounds(nx, ny, size):
                yield nx, ny


def generate_ship_map(size: int = 50, openness: float = 0.5, seed: int | None = None) -> Grid:
    """Generate a connected maze-like ship map.

    Args:
        size: Width and height of the square grid.
        openness: Fraction of dead ends to reduce after the initial maze is carved.
        seed: Optional random seed for reproducible experiments.

    Returns:
        A square grid where OPEN = traversable hallway and BLOCKED = wall.
    """
    if size < 4:
        raise ValueError("size must be at least 4")
    if not 0 <= openness <= 1:
        raise ValueError("openness must be between 0 and 1")

    rng = random.Random(seed)
    grid: Grid = [[BLOCKED for _ in range(size)] for _ in range(size)]

    start = (rng.randint(1, size - 2), rng.randint(1, size - 2))
    grid[start[0]][start[1]] = OPEN

    while True:
        candidates: list[Cell] = []
        for x in range(1, size - 1):
            for y in range(1, size - 1):
                if grid[x][y] == BLOCKED:
                    open_count = sum(grid[nx][ny] == OPEN for nx, ny in cardinal_neighbors(x, y, size))
                    if open_count == 1:
                        candidates.append((x, y))
        if not candidates:
            break
        x, y = rng.choice(candidates)
        grid[x][y] = OPEN

    def dead_ends() -> list[Cell]:
        return [
            (x, y)
            for x in range(1, size - 1)
            for y in range(1, size - 1)
            if grid[x][y] == OPEN
            and sum(grid[nx][ny] == OPEN for nx, ny in cardinal_neighbors(x, y, size)) == 1
        ]

    current_dead_ends = dead_ends()
    target_count = int(len(current_dead_ends) * (1 - openness))

    while len(current_dead_ends) > target_count:
        x, y = rng.choice(current_dead_ends)
        blocked_neighbors = [(nx, ny) for nx, ny in cardinal_neighbors(x, y, size) if grid[nx][ny] == BLOCKED]
        if blocked_neighbors:
            nx, ny = rng.choice(blocked_neighbors)
            grid[nx][ny] = OPEN
        current_dead_ends = dead_ends()

    return grid


def random_open_cell(grid: Grid, rng: random.Random | None = None) -> Cell:
    rng = rng or random
    open_cells = [(x, y) for x, row in enumerate(grid) for y, value in enumerate(row) if value == OPEN]
    if not open_cells:
        raise ValueError("grid has no open cells")
    return rng.choice(open_cells)


def render_grid(grid: Grid) -> str:
    return "\n".join("".join("." if cell == OPEN else "#" for cell in row) for row in grid)
