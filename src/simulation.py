"""Experiment runner for autonomous maze exploration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Type

from bots import BasicBot, Bot, SensoryBot
from maze_map import generate_ship_map, random_open_cell
from strategies import FarthestFrontierStrategy, InformationGainStrategy, NearestFrontierStrategy, Strategy


@dataclass
class TrialResult:
    bot_type: str
    strategy: str
    movements: int
    blocked_attempts: int
    planning_nodes: int
    identified_ratio: float
    completed: bool
    steps: int


BOT_TYPES: dict[str, Type[Bot]] = {
    "basic": BasicBot,
    "sensory": SensoryBot,
}

STRATEGIES: dict[str, Type[Strategy]] = {
    "nearest_frontier": NearestFrontierStrategy,
    "farthest_frontier": FarthestFrontierStrategy,
    "information_gain": InformationGainStrategy,
}


def run_trial(
    bot_name: str,
    strategy_name: str,
    size: int = 30,
    openness: float = 0.5,
    seed: int | None = None,
    max_steps: int | None = None,
) -> TrialResult:
    true_map = generate_ship_map(size=size, openness=openness, seed=seed)
    start = random_open_cell(true_map)
    bot = BOT_TYPES[bot_name](start, true_map)
    strategy = STRATEGIES[strategy_name]()

    max_steps = max_steps or size * size * 3
    planning_nodes = 0
    steps = 0
    stalled_steps = 0

    while bot.has_unknown_cells() and steps < max_steps:
        plan = strategy.next_move(bot)
        planning_nodes += plan.processed_nodes
        if plan.move == (0, 0):
            stalled_steps += 1
            if stalled_steps >= 5:
                break
        else:
            stalled_steps = 0
            bot.try_move(*plan.move)
        steps += 1

    return TrialResult(
        bot_type=bot_name,
        strategy=strategy_name,
        movements=bot.movements,
        blocked_attempts=bot.blocked_attempts,
        planning_nodes=planning_nodes,
        identified_ratio=bot.identified_ratio(),
        completed=not bot.has_unknown_cells(),
        steps=steps,
    )


def run_experiments(size: int = 30, openness: float = 0.5, trials: int = 10) -> list[TrialResult]:
    results: list[TrialResult] = []
    seed = 1000
    for bot_name in BOT_TYPES:
        for strategy_name in STRATEGIES:
            for trial in range(trials):
                results.append(
                    run_trial(
                        bot_name=bot_name,
                        strategy_name=strategy_name,
                        size=size,
                        openness=openness,
                        seed=seed + trial,
                    )
                )
    return results


def summarize(results: list[TrialResult]) -> list[dict[str, float | str]]:
    grouped: dict[tuple[str, str], list[TrialResult]] = {}
    for result in results:
        grouped.setdefault((result.bot_type, result.strategy), []).append(result)

    rows: list[dict[str, float | str]] = []
    for (bot_type, strategy), items in sorted(grouped.items()):
        n = len(items)
        rows.append(
            {
                "bot_type": bot_type,
                "strategy": strategy,
                "avg_movements": sum(item.movements for item in items) / n,
                "avg_blocked_attempts": sum(item.blocked_attempts for item in items) / n,
                "avg_planning_nodes": sum(item.planning_nodes for item in items) / n,
                "avg_identified_ratio": sum(item.identified_ratio for item in items) / n,
                "completion_rate": sum(item.completed for item in items) / n,
            }
        )
    return rows
