import random


def evolve(
    initialise,
    fitness,
    select,
    crossover,
    mutate,
    population_size,
    generations,
    crossover_rate,
    mutation_rate,
    elites,
    is_solved=None,
):
    # is_solved(individual) -> bool stops the run early; None means always run every generation
    # crossover and mutate must return new individuals, because parents and elites are shared
    population = initialise(population_size)
    history = []  # best fitness per generation, i.e. the convergence curve

    for generation in range(generations + 1):
        fitness_scores = [fitness(individual) for individual in population]
        ranked = sorted(
            range(population_size), key=lambda i: fitness_scores[i], reverse=True
        )
        best = population[ranked[0]]
        best_score = fitness_scores[ranked[0]]
        history.append(best_score)

        solved = is_solved is not None and is_solved(best)
        if solved or generation == generations:
            return best, history

        next_population = [population[i] for i in ranked[:elites]]

        while len(next_population) < population_size:
            parent_a = select(population, fitness_scores)
            parent_b = select(population, fitness_scores)

            if random.random() < crossover_rate:
                children = crossover(parent_a, parent_b)
            else:
                children = parent_a, parent_b

            for child in children:
                if len(next_population) < population_size:
                    if random.random() < mutation_rate:
                        child = mutate(child)
                    next_population.append(child)

        population = next_population
