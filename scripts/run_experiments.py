"""Run maze exploration experiments and generate summary plots."""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import matplotlib.pyplot as plt

from simulation import run_experiments, summarize


def write_summary_csv(rows, output_dir: Path) -> None:
    with open(output_dir / "summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def plot_metric(rows, metric: str, ylabel: str, filename: str, output_dir: Path) -> None:
    labels = [f"{row['bot_type']}\n{row['strategy'].replace('_', ' ')}" for row in rows]
    values = [row[metric] for row in rows]

    plt.figure(figsize=(11, 5))
    plt.bar(labels, values)
    plt.xticks(rotation=35, ha="right")
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(output_dir / filename, dpi=160)
    plt.close()


def main() -> None:
    output_dir = PROJECT_ROOT / "outputs"
    figure_dir = PROJECT_ROOT / "figures"
    output_dir.mkdir(exist_ok=True)
    figure_dir.mkdir(exist_ok=True)

    results = run_experiments(size=20, openness=0.5, trials=5)
    rows = summarize(results)

    write_summary_csv(rows, output_dir)
    plot_metric(rows, "avg_movements", "Average successful movements", "movement_comparison.png", output_dir)
    plot_metric(rows, "avg_identified_ratio", "Average identified map ratio", "coverage_comparison.png", output_dir)
    plot_metric(rows, "avg_planning_nodes", "Average BFS planning nodes processed", "planning_comparison.png", output_dir)

    # Keep publication-ready copies in figures/ for GitHub README.
    for filename in ("movement_comparison.png", "coverage_comparison.png", "planning_comparison.png"):
        (figure_dir / filename).write_bytes((output_dir / filename).read_bytes())

    print("Saved experiment results in outputs/ and README figures in figures/.")


if __name__ == "__main__":
    main()
