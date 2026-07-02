"""Exploration strategies based on frontier selection and BFS planning."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

from bots import UNKNOWN, Bot
from maze_map import OPEN

Cell = Tuple[int, int]
Move = Tuple[int, int]


@dataclass
class MovePlan:
    move: Move
    processed_nodes: int


class Strategy:
    name = "base"

    def next_move(self, bot: Bot) -> MovePlan:
        raise NotImplementedError

    @staticmethod
    def adjacent_unknowns(bot: Bot) -> list[Cell]:
        x, y = bot.position
        return [
            (nx, ny)
            for nx, ny in bot.neighbors(x, y)
            if bot.knowledge[nx][ny] == UNKNOWN
        ]

    @staticmethod
    def frontier_cells(bot: Bot) -> list[Cell]:
        frontiers: list[Cell] = []
        for x in range(bot.size):
            for y in range(bot.size):
                if bot.knowledge[x][y] == OPEN and any(
                    bot.knowledge[nx][ny] == UNKNOWN for nx, ny in bot.neighbors(x, y)
                ):
                    frontiers.append((x, y))
        return frontiers

    @staticmethod
    def choose_unknown_step(bot: Bot, unknown_cells: list[Cell]) -> MovePlan:
        target = unknown_cells[0]
        return MovePlan((target[0] - bot.x, target[1] - bot.y), processed_nodes=1)

    @staticmethod
    def bfs_to_targets(bot: Bot, targets: set[Cell]) -> tuple[list[Cell], int]:
        start = bot.position
        queue = deque([(start, [start])])
        visited = {start}
        processed = 0

        while queue:
            (x, y), path = queue.popleft()
            processed += 1
            if (x, y) in targets:
                return path, processed
            for nx, ny in bot.neighbors(x, y):
                if (nx, ny) not in visited and bot.knowledge[nx][ny] == OPEN:
                    visited.add((nx, ny))
                    queue.append(((nx, ny), path + [(nx, ny)]))
        return [start], processed


class NearestFrontierStrategy(Strategy):
    """Move toward the closest known open cell adjacent to unknown territory."""

    name = "nearest_frontier"

    def next_move(self, bot: Bot) -> MovePlan:
        adjacent = self.adjacent_unknowns(bot)
        if adjacent:
            return self.choose_unknown_step(bot, adjacent)

        frontiers = self.frontier_cells(bot)
        if not frontiers:
            return MovePlan((0, 0), 0)

        path, processed = self.bfs_to_targets(bot, set(frontiers))
        if len(path) < 2:
            return MovePlan((0, 0), processed)
        next_x, next_y = path[1]
        return MovePlan((next_x - bot.x, next_y - bot.y), processed)


class FarthestFrontierStrategy(Strategy):
    """Move toward the farthest reachable frontier to expand the known map broadly."""

    name = "farthest_frontier"

    def next_move(self, bot: Bot) -> MovePlan:
        adjacent = self.adjacent_unknowns(bot)
        if adjacent:
            return self.choose_unknown_step(bot, adjacent)

        frontiers = self.frontier_cells(bot)
        if not frontiers:
            return MovePlan((0, 0), 0)

        distances = self._reachable_distances(bot)
        reachable_frontiers = [cell for cell in frontiers if cell in distances]
        if not reachable_frontiers:
            return MovePlan((0, 0), len(distances))

        target = max(reachable_frontiers, key=lambda cell: distances[cell])
        path, processed = self.bfs_to_targets(bot, {target})
        if len(path) < 2:
            return MovePlan((0, 0), processed)
        next_x, next_y = path[1]
        return MovePlan((next_x - bot.x, next_y - bot.y), processed)

    @staticmethod
    def _reachable_distances(bot: Bot) -> dict[Cell, int]:
        start = bot.position
        queue = deque([(start, 0)])
        distances = {start: 0}
        while queue:
            (x, y), dist = queue.popleft()
            for nx, ny in bot.neighbors(x, y):
                if (nx, ny) not in distances and bot.knowledge[nx][ny] == OPEN:
                    distances[(nx, ny)] = dist + 1
                    queue.append(((nx, ny), dist + 1))
        return distances


class InformationGainStrategy(Strategy):
    """Score frontier cells by nearby unknown cells, with a distance penalty."""

    name = "information_gain"

    def next_move(self, bot: Bot) -> MovePlan:
        adjacent = self.adjacent_unknowns(bot)
        if adjacent:
            # Prefer the adjacent unknown with the most unknown neighbors around it.
            target = max(adjacent, key=lambda cell: self._local_unknown_count(bot, cell))
            return MovePlan((target[0] - bot.x, target[1] - bot.y), processed_nodes=1)

        frontiers = self.frontier_cells(bot)
        if not frontiers:
            return MovePlan((0, 0), 0)

        distances = FarthestFrontierStrategy._reachable_distances(bot)
        reachable_frontiers = [cell for cell in frontiers if cell in distances]
        if not reachable_frontiers:
            return MovePlan((0, 0), len(distances))

        def score(cell: Cell) -> float:
            unknown_gain = self._local_unknown_count(bot, cell)
            return unknown_gain - 0.15 * distances[cell]

        target = max(reachable_frontiers, key=score)
        path, processed = self.bfs_to_targets(bot, {target})
        if len(path) < 2:
            return MovePlan((0, 0), processed)
        next_x, next_y = path[1]
        return MovePlan((next_x - bot.x, next_y - bot.y), processed)

    @staticmethod
    def _local_unknown_count(bot: Bot, cell: Cell) -> int:
        x, y = cell
        count = 0
        for nx, ny in bot.neighbors(x, y):
            if bot.knowledge[nx][ny] == UNKNOWN:
                count += 1
        return count
