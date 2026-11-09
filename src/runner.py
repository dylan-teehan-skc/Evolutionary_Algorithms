import random
from functools import partial

from src.crossover import one_point_crossover, subtree_crossover
from src.evolution import evolve
from src.fitness import negative_error, one_max
from src.initialisation import ramped_half_and_half, random_bitstrings
from src.mutation import bit_flip_mutation, grow_mutation
from src.selection import roulette_selection, tournament_selection
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
SELECTIONS = {"tournament": tournament_selection, "roulette": roulette_selection}


def selection(config):
    method = config["selection"]["method"]
    # each method reads only its own block, so a method with no settings needs no block
    return partial(SELECTIONS[method], **config["selection"].get(method, {}))


def run(config):
    # every operator uses the global random module, so one seed fixes the whole run
    random.seed(config["seed"])
    print("Seed:", config["seed"])
    algorithm = config["algorithm"]
    operators, describe = ALGORITHMS[algorithm](config)

    best = evolve(
        select=selection(config),
        target_fitness=config["target_fitness"][algorithm],
        **operators,
        **config["evolution"],
    )
    print("Best:", describe(best))
    print("Fitness:", operators["fitness"](best))
