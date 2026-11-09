from functools import partial

from src.crossover import one_point_crossover, subtree_crossover
from src.evolution import evolve
from src.fitness import negative_error, one_max
from src.initialisation import ramped_half_and_half, random_bitstrings
from src.mutation import bit_flip_mutation, grow_mutation
from src.selection import tournament_selection
from src.tree import to_expression


def ga_operators(config):
    operators = {
        "initialise": partial(
            random_bitstrings, **config["initialisation"]["bitstrings"]
        ),
        "fitness": one_max,
        "crossover": one_point_crossover,
        "mutate": bit_flip_mutation,
    }
    return operators, str


def gp_operators(config):
    trees = config["initialisation"]["trees"]
    operators = {
        "initialise": partial(ramped_half_and_half, **trees),
        "fitness": partial(negative_error, points=config["points"]),
        "crossover": partial(subtree_crossover, **trees),
        "mutate": partial(grow_mutation, **trees),
    }
    return operators, to_expression


ALGORITHMS = {"ga": ga_operators, "gp": gp_operators}


def run(config):
    algorithm = config["algorithm"]
    operators, describe = ALGORITHMS[algorithm](config)

    best = evolve(
        select=partial(tournament_selection, **config["selection"]),
        target_fitness=config["target_fitness"][algorithm],
        **operators,
        **config["evolution"],
    )
    print("Best:", describe(best))
    print("Fitness:", operators["fitness"](best))
