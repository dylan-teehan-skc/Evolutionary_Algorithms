import random
from functools import partial

from src.benchmarks import points
from src.crossover import one_point_crossover, subtree_crossover
from src.evolution import evolve
from src.fitness import all_hits, negative_error, one_max
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
    target = config["success"]["ga"]
    return operators, (lambda bits: one_max(bits) >= target), str


def gp_operators(config):
    trees = config["initialisation"]["trees"]
    data = points(config["problem"])
    operators = {
        "initialise": partial(ramped_half_and_half, **trees),
        "fitness": partial(negative_error, points=data),
        "crossover": partial(subtree_crossover, **trees),
        "mutate": partial(grow_mutation, **trees),
    }
    is_solved = partial(all_hits, points=data, threshold=config["success"]["gp"])
    return operators, is_solved, to_expression


ALGORITHMS = {"ga": ga_operators, "gp": gp_operators}
SELECTIONS = {"tournament": tournament_selection, "roulette": roulette_selection}


def selection(config):
    method = config["selection"]["method"]
    # each method reads only its own block, so a method with no settings needs no block
    return partial(SELECTIONS[method], **config["selection"].get(method, {}))


def run_once(config, seed):
    # every operator uses the global random module, so one seed fixes the whole run
    random.seed(seed)
    algorithm = config["algorithm"]
    operators, is_solved, describe = ALGORITHMS[algorithm](config)

    best, history = evolve(
        select=selection(config),
        is_solved=is_solved,
        **operators,
        **config["evolution"],
    )
    return {
        "seed": seed,
        "best": describe(best),
        "fitness": history[-1],  # evolve returns the best of the last generation scored
        "generations": len(history) - 1,
        "solved": is_solved(best),
        "history": history,
    }


def run(config):
    result = run_once(config, config["seed"])
    print("Seed:", result["seed"])
    for generation, score in enumerate(result["history"]):
        print(generation, score)
    print("Best:", result["best"])
    print("Fitness:", result["fitness"])
