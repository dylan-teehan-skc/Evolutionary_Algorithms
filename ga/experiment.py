import csv
import statistics
from pathlib import Path

import yaml

from src.runner import run_once


def summarise(results, population_size):
    finals = [r["fitness"] for r in results]
    solved = [r for r in results if r["solved"]]
    summary = {
        "runs": len(results),
        "best": max(finals),
        "worst": min(finals),
        "mean": statistics.mean(finals),
        "median": statistics.median(finals),
        "stdev": statistics.stdev(finals) if len(finals) > 1 else 0.0,
        "success_rate": len(solved) / len(results),
    }
    if solved:
        # generation 0 counts as one round of evaluations, so a run that stops at gen g used g+1
        evaluations = [(r["generations"] + 1) * population_size for r in solved]
        summary["mean_evals_to_target"] = statistics.mean(evaluations)
    return summary


def write_results(results, path):
    # one row per run, then one row per (run, generation) for the convergence curves
    path.parent.mkdir(exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["seed", "fitness", "generations", "solved", "best"])
        for r in results:
            writer.writerow([r["seed"], r["fitness"], r["generations"], r["solved"], r["best"]])

    convergence = path.with_name(path.stem + "_convergence.csv")
    with convergence.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["seed", "generation", "best_fitness"])
        for r in results:
            for generation, score in enumerate(r["history"]):
                writer.writerow([r["seed"], generation, score])
    return convergence


if __name__ == "__main__":
    config = yaml.safe_load(Path(__file__).with_name("config.yaml").read_text())
    seeds = range(config["seed"], config["seed"] + config["runs"])
    results = []
    for seed in seeds:
        result = run_once(config, seed)
        results.append(result)
        print(f"seed {seed}: fitness {result['fitness']} after {result['generations']} generations")

    name = f"ga_{config['selection']['method']}"
    path = Path(__file__).with_name("results") / f"{name}.csv"
    convergence = write_results(results, path)

    print(f"\n{name}, seeds {seeds.start}-{seeds.stop - 1}")
    for key, value in summarise(results, config["evolution"]["population_size"]).items():
        print(f"  {key}: {value:g}" if isinstance(value, float) else f"  {key}: {value}")
    print(f"Saved {path.name} and {convergence.name} in results/")
