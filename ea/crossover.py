import random


def one_point_crossover(parent_a, parent_b):
    cut = random.randint(1, len(parent_a) - 1)
    return (parent_a[:cut] + parent_b[cut:], parent_b[:cut] + parent_a[cut:])
