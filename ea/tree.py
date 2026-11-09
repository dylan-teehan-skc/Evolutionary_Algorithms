import random

from treelib import Tree

FUNCTIONS = {"+": 2, "-": 2, "*": 2}  # symbol -> arity
TERMINALS = ["x", 1.0]


def random_tree(max_depth, full):
    # full: every branch reaches max_depth. grow: branches may stop early on a terminal.
    tree = Tree()

    def build(parent, depth):
        if depth == max_depth:
            options = TERMINALS  # leaves must be terminals
        elif full:
            options = list(FUNCTIONS)
        else:
            options = list(FUNCTIONS) + TERMINALS
        symbol = random.choice(options)
        node = tree.create_node(str(symbol), parent=parent, data=symbol)
        for _ in range(FUNCTIONS.get(symbol, 0)):
            build(node.identifier, depth + 1)

    build(None, 0)
    return tree


def is_valid(tree, max_depth):
    # every function node has arity children, so every leaf is a terminal
    return tree.depth() <= max_depth and all(
        len(tree.children(node.identifier)) == FUNCTIONS.get(node.data, 0)
        for node in tree.all_nodes_itr()
    )
