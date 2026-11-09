import random
from functools import partial

from src.crossover import one_point_crossover
from src.evolution import evolve
from src.fitness import one_max
from src.initialisation import random_bitstrings
from src.mutation import bit_flip_mutation
from src.selection import roulette_selection, tournament_selection

SELECTIONS = {"tournament": tournament_selection, "roulette": roulette_selection}


def selection(config):
    method = config["selection"]["method"]
    # each method reads only its own block, so a method with no settings needs no block
    return partial(SELECTIONS[method], **config["selection"].get(method, {}))


def run_once(config, seed):
    # every operator uses the global random module, so one seed fixes the whole run
    random.seed(seed)
    target = config["success"]
    is_solved = lambda bits: one_max(bits) >= target

    best, history = evolve(
        initialise=partial(random_bitstrings, length=config["length"]),
        fitness=one_max,
        select=selection(config),
        crossover=one_point_crossover,
        mutate=bit_flip_mutation,
        is_solved=is_solved,
        **config["evolution"],
    )
    return {
        "seed": seed,
        "best": str(best),
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
