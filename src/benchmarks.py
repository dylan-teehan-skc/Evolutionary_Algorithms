import math
import random

# Nguyen symbolic regression suite as defined in Uy et al. (2011), Table 1.
# name -> (target function, sample range). Each uses 20 points drawn uniformly from the range.
BENCHMARKS = {
    "nguyen-1": (lambda x: x**3 + x**2 + x, (-1, 1)),
    "nguyen-2": (lambda x: x**4 + x**3 + x**2 + x, (-1, 1)),  # Koza's (1992) quartic
    "nguyen-5": (lambda x: math.sin(x**2) * math.cos(x) - 1, (-1, 1)),
    "nguyen-7": (lambda x: math.log(x + 1) + math.log(x**2 + 1), (0, 2)),
}
SAMPLES = 20


def points(name, data_seed=0):
    # own generator so every run and every config trains on the same 20 points,
    # independent of the run seed that drives evolution
    target, (low, high) = BENCHMARKS[name]
    rng = random.Random(data_seed)
    return [(x, target(x)) for x in (rng.uniform(low, high) for _ in range(SAMPLES))]
