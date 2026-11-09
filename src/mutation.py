import random

from treelib import Tree

from src.tree import FUNCTIONS, TERMINALS


def bit_flip_mutation(bits):
    mutated = bits[:]
    mutated[random.randrange(len(mutated))] ^= 1
    return mutated


def grow_mutation(tree, max_tree_depth):
    mutated = Tree(tree, deep=True)
    leaf = random.choice(mutated.leaves())

    if mutated.depth(leaf) < max_tree_depth:
        leaf.data = random.choice(list(FUNCTIONS))
        for _ in range(FUNCTIONS[leaf.data]):
            terminal = random.choice(TERMINALS)
            mutated.create_node(str(terminal), parent=leaf.identifier, data=terminal)
    else:
        leaf.data = random.choice([t for t in TERMINALS if t != leaf.data])
    leaf.tag = str(leaf.data)
    return mutated
