import random

from src.tree import random_tree


def ramped_half_and_half(population_size, max_tree_depth):
    # alternate full/grow, and ramp depth 1..max_tree_depth across the population
    return [
        random_tree(1 + (i // 2) % max_tree_depth, full=i % 2 == 0)
        for i in range(population_size)
    ]
