import random
from functools import partial

from src.benchmarks import points
from src.crossover import subtree_crossover
from src.evolution import evolve
from src.fitness import all_hits, negative_error
from src.initialisation import ramped_half_and_half
from src.mutation import grow_mutation
from src.selection import roulette_selection, tournament_selection
from src.tree import to_expression

SELECTIONS = {"tournament": tournament_selection, "roulette": roulette_selection}


def selection(config):
    method = config["selection"]["method"]
    # each method reads only its own block, so a method with no settings needs no block
    return partial(SELECTIONS[method], **config["selection"].get(method, {}))


def run_once(config, seed):
    # every operator uses the global random module, so one seed fixes the whole run
    random.seed(seed)
    depth = {"max_tree_depth": config["max_tree_depth"]}
    data = points(config["problem"])
    is_solved = partial(all_hits, points=data, threshold=config["success"])

    best, history = evolve(
        initialise=partial(ramped_half_and_half, **depth),
        fitness=partial(negative_error, points=data),
        select=selection(config),
        crossover=partial(subtree_crossover, **depth),
        mutate=partial(grow_mutation, **depth),
        is_solved=is_solved,
        **config["evolution"],
    )
    return {
        "seed": seed,
        "best": to_expression(best),
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
