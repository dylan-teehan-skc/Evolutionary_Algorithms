import math
import operator
import random

from anytree import Node, PreOrderIter


def protected_div(a, b):
    return a / b if b != 0 else 1.0  # Koza (1992): x/0 = 1 so every tree can be evaluated


def protected_log(a):
    return math.log(abs(a)) if a != 0 else 0.0  # log|x|, defined for negatives and 0


# The Nguyen function and terminal sets (Uy et al. 2011): symbol -> (arity, implementation)
PRIMITIVES = {
    "+": (2, operator.add),
    "-": (2, operator.sub),
    "*": (2, operator.mul),
    "/": (2, protected_div),
    "sin": (1, math.sin),
    "cos": (1, math.cos),
    "exp": (1, math.exp),
    "log": (1, protected_log),
}
FUNCTIONS = {symbol: arity for symbol, (arity, _) in PRIMITIVES.items()}
TERMINALS = ["x"]

# a tree is its root Node: node.name is the symbol, node.children its arguments in order


def random_tree(max_depth, full):
    # full: every branch reaches max_depth. grow: branches may stop early on a terminal.
    def build(depth):
        if depth == max_depth:
            options = TERMINALS  # leaves must be terminals
        elif full:
            options = list(FUNCTIONS)
        else:
            options = list(FUNCTIONS) + TERMINALS
        symbol = random.choice(options)
        children = [build(depth + 1) for _ in range(FUNCTIONS.get(symbol, 0))]
        return Node(symbol, children=children)

    return build(0)


def is_valid(tree, max_depth):
    # every function node has arity children, so every leaf is a terminal
    return tree.height <= max_depth and all(
        len(node.children) == FUNCTIONS.get(node.name, 0) for node in PreOrderIter(tree)
    )


def copy_tree(node):
    return Node(node.name, children=[copy_tree(child) for child in node.children])


def graft(node, target, donor):
    # returns a new tree, because parents are shared with elites and must not change
    if node is target:
        return copy_tree(donor)
    return Node(node.name, children=[graft(c, target, donor) for c in node.children])


def to_expression(node):
    if node.is_leaf:
        return str(node.name)
    arguments = [to_expression(child) for child in node.children]
    if len(arguments) == 1:
        return f"{node.name}({arguments[0]})"
    left, right = arguments
    return f"({left} {node.name} {right})"
