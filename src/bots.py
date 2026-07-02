"""Bot models for exploring an initially unknown maze."""

from __future__ import annotations

from typing import List, Tuple

from maze_map import BLOCKED, OPEN, Grid, cardinal_neighbors, in_bounds, surrounding_cells

UNKNOWN = -1
Cell = Tuple[int, int]


class Bot:
    """Base bot with shared map knowledge and movement bookkeeping."""

    def __init__(self, start: Cell, true_map: Grid):
        self.x, self.y = start
        self.true_map = true_map
        self.size = len(true_map)
        self.knowledge: Grid = [[UNKNOWN for _ in range(self.size)] for _ in range(self.size)]
        self.knowledge[self.x][self.y] = OPEN
        self.movements = 0
        self.blocked_attempts = 0
        self.move_history: list[Cell] = [start]

    @property
    def position(self) -> Cell:
        return self.x, self.y

    def in_bounds(self, x: int, y: int) -> bool:
        return in_bounds(x, y, self.size)

    def neighbors(self, x: int, y: int):
        return cardinal_neighbors(x, y, self.size)

    def update_cell(self, x: int, y: int, state: int) -> None:
        if self.in_bounds(x, y):
            self.knowledge[x][y] = state

    def try_move(self, dx: int, dy: int) -> bool:
        nx, ny = self.x + dx, self.y + dy
        if not self.in_bounds(nx, ny):
            return False
        if self.true_map[nx][ny] == BLOCKED:
            self.update_cell(nx, ny, BLOCKED)
            self.blocked_attempts += 1
            return False
        self.x, self.y = nx, ny
        self.update_cell(nx, ny, OPEN)
        self.movements += 1
        self.move_history.append((nx, ny))
        return True

    def identified_count(self) -> int:
        return sum(cell != UNKNOWN for row in self.knowledge for cell in row)

    def identified_ratio(self) -> float:
        return self.identified_count() / (self.size * self.size)

    def has_unknown_cells(self) -> bool:
        return self.identified_count() < self.size * self.size


class BasicBot(Bot):
    """Learns walls only by attempting to move into neighboring cells."""

    pass


class SensoryBot(Bot):
    """Senses the blocked/open state of the eight surrounding cells after each move."""

    def __init__(self, start: Cell, true_map: Grid):
        super().__init__(start, true_map)
        self.sense_surroundings()

    def sense_surroundings(self) -> None:
        for nx, ny in surrounding_cells(self.x, self.y, self.size):
            self.update_cell(nx, ny, self.true_map[nx][ny])

    def try_move(self, dx: int, dy: int) -> bool:
        moved = super().try_move(dx, dy)
        self.sense_surroundings()
        return moved
