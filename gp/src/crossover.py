import random

from src.tree import graft


def subtree_crossover(parent_a, parent_b, max_tree_depth):
    node_a = random.choice(list(parent_a.nodes))
    node_b = random.choice(list(parent_b.nodes))
    child_a = graft(parent_a, node_a, parent_b, node_b)
    child_b = graft(parent_b, node_b, parent_a, node_a)
    # a child over the depth limit is dropped and its parent survives instead
    return (
        child_a if child_a.depth() <= max_tree_depth else parent_a,
        child_b if child_b.depth() <= max_tree_depth else parent_b,
    )
