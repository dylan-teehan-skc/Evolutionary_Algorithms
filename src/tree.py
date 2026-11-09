import math
import operator
import random

from treelib import Tree


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


def _copy_node(source, node_id, target, parent_id):
    node = source[node_id]
    return target.create_node(node.tag, parent=parent_id, data=node.data).identifier


def _copy_subtree(source, node_id, target, parent_id):
    new_id = _copy_node(source, node_id, target, parent_id)
    for child in source.children(node_id):
        _copy_subtree(source, child.identifier, target, new_id)


def graft(tree, target_id, donor, donor_id):
    # treelib's paste changes argument order and fails on duplicate ids, so rebuild instead
    grafted = Tree()

    def copy_around_target(node_id, parent_id):
        if node_id == target_id:
            _copy_subtree(donor, donor_id, grafted, parent_id)
            return
        new_id = _copy_node(tree, node_id, grafted, parent_id)
        for child in tree.children(node_id):
            copy_around_target(child.identifier, new_id)

    copy_around_target(tree.root, None)
    return grafted


def to_expression(tree, node_id=None):
    node_id = tree.root if node_id is None else node_id
    children = tree.children(node_id)
    if not children:
        return tree[node_id].tag
    arguments = [to_expression(tree, c.identifier) for c in children]
    if len(arguments) == 1:
        return f"{tree[node_id].tag}({arguments[0]})"
    left, right = arguments
    return f"({left} {tree[node_id].tag} {right})"
