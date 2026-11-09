from functools import partial
from pathlib import Path

import yaml

from ea.crossover import one_point_crossover
from ea.evolution import evolve
from ea.fitness import one_max
from ea.initialisation import random_bitstrings
from ea.mutation import bit_flip_mutation
from ea.selection import tournament_selection


def main():
    config_path = Path(__file__).with_name("config.yaml")
    config = yaml.safe_load(config_path.read_text())

    best = evolve(
        initialise=partial(random_bitstrings, **config["initialisation"]["bitstrings"]),
        fitness=one_max,
        select=partial(tournament_selection, **config["selection"]),
        crossover=one_point_crossover,
        mutate=bit_flip_mutation,
        **config["evolution"],
    )
    print("Best:", best)
    print("Fitness:", one_max(best))


if __name__ == "__main__":
    main()
