import random

from anytree import Node

from src.tree import TERMINALS, graft, random_tree


def grow_mutation(tree, max_tree_depth):
    leaf = random.choice(tree.leaves)
    if leaf.depth < max_tree_depth:
        replacement = random_tree(1, full=True)  # one function with terminal children
    else:
        # swap for a different terminal; with a single terminal there is nothing to swap to
        others = [t for t in TERMINALS if t != leaf.name] or TERMINALS
        replacement = Node(random.choice(others))
    return graft(tree, leaf, replacement)
