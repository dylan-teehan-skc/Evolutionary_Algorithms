import random


def random_bitstrings(population_size, length):
    return [
        [random.randint(0, 1) for _ in range(length)] for _ in range(population_size)
    ]
