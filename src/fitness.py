import operator

OPERATIONS = {"+": operator.add, "-": operator.sub, "*": operator.mul}


def one_max(bits):
    return sum(bits)


def evaluate(tree, inputs, node_id=None):
    node_id = tree.root if node_id is None else node_id
    symbol = tree[node_id].data
    children = tree.children(node_id)
    if not children:
        return inputs.get(symbol, symbol)
    arguments = [evaluate(tree, inputs, child.identifier) for child in children]
    return OPERATIONS[symbol](*arguments)


def negative_error(tree, points):
    # evolve maximises, so a perfect tree scores 0
    return 0 - sum(abs(evaluate(tree, {"x": x}) - y) for x, y in points)
