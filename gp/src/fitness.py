import math

from src.tree import PRIMITIVES

# ponytail: one flat cap for broken trees, revisit if real errors ever get near it
MAX_ERROR = 1e12


def evaluate(node, inputs):
    if node.is_leaf:
        return inputs.get(node.name, node.name)
    arguments = [evaluate(child, inputs) for child in node.children]
    return PRIMITIVES[node.name][1](*arguments)


def point_error(tree, x, y):
    # exp overflows and sin(inf) raises, so any tree that blows up gets the worst error
    try:
        error = abs(evaluate(tree, {"x": x}) - y)
    except (OverflowError, ValueError):
        return MAX_ERROR
    return error if math.isfinite(error) else MAX_ERROR


def negative_error(tree, points):
    # evolve maximises, so a perfect tree scores 0
    return 0 - min(sum(point_error(tree, x, y) for x, y in points), MAX_ERROR)  # 0 - avoids -0.0


def all_hits(tree, points, threshold):
    # Uy et al. (2011): a run succeeds when every point is a hit, i.e. error below threshold
    return all(point_error(tree, x, y) < threshold for x, y in points)
