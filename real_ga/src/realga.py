# Real-coded GA on [0,1]^n with one seeded random.Random per run (ENG-01..09).


def initialise(rng, size, n):
    return [[rng.random() for _ in range(n)] for _ in range(size)]


def tournament(rng, population, scores, size, replace=True):
    picks = rng.choices(range(len(population)), k=size) if replace else rng.sample(range(len(population)), size)
    return population[max(picks, key=lambda i: scores[i])]


def blend(rng, a, b):
    # arithmetic crossover: one weight per gene, children mirror each other
    c, d = [], []
    for x, y in zip(a, b):
        w = rng.random()
        c.append(w * x + (1 - w) * y)
        d.append((1 - w) * x + w * y)
    return c, d


def mutate(rng, genome, prob, sigma):
    return [min(1.0, max(0.0, x + rng.gauss(0, sigma))) if rng.random() < prob else x for x in genome]


def _record(history, population, scores, used):
    best = max(range(len(population)), key=lambda i: scores[i])
    history.append({"gen": len(history), "best_score": scores[best], "best_genome": list(population[best]),
                    "evaluations": used})


def _result(history, used):
    last = history[-1]
    return {"best_genome": last["best_genome"], "best_score": last["best_score"], "history": history,
            "evaluations": used}


def evolve(evaluate, n, s, seed):
    # every evaluate call is a budget unit; elites keep their scores and are never re-evaluated
    import random
    rng = random.Random(seed)
    budget = s["max_evaluations"]
    population = initialise(rng, min(s["population_size"], budget), n)
    cache = {}

    def score(g):
        # a genome scored before reuses its score and costs no budget (ENG-05)
        key = tuple(g)
        if key not in cache:
            cache[key] = evaluate(g)
        return cache[key]

    scores = [score(g) for g in population]
    used, history = len(cache), []
    _record(history, population, scores, used)
    while used < budget:
        ranked = sorted(range(len(population)), key=lambda i: scores[i], reverse=True)
        next_pop = [population[i] for i in ranked[:s["elites"]]]
        next_scores = [scores[i] for i in ranked[:s["elites"]]]
        children = []
        want = min(s["population_size"] - len(next_pop), budget - used)
        while len(children) < want:
            a = tournament(rng, population, scores, s["tournament_size"])
            b = tournament(rng, population, scores, s["tournament_size"])
            for c in blend(rng, a, b):
                children.append(mutate(rng, c, s["mutation_prob"], s["mutation_sigma"]))
        children = children[:want]
        next_pop += children
        next_scores += [score(g) for g in children]
        used = len(cache)
        population, scores = next_pop, next_scores
        _record(history, population, scores, used)
    return _result(history, used)


def random_search(evaluate, n, s, seed):
    # same budget and result shape; "generations" are batches of population_size samples
    import random
    rng = random.Random(seed)
    best_g, best_s, used, history = None, None, 0, []
    while used < s["max_evaluations"]:
        batch = initialise(rng, min(s["population_size"] - (s["elites"] if history else 0), s["max_evaluations"] - used), n)
        for g in batch:
            v = evaluate(g)
            if best_s is None or v > best_s:
                best_g, best_s = g, v
        used += len(batch)
        _record(history, [best_g], [best_s], used)
    return _result(history, used)
