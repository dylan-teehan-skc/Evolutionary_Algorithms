import random


def tournament_selection(population, fitness_scores, tournament_size=3):
    contestants = random.sample(range(len(population)), tournament_size)
    winner = max(contestants, key=lambda i: fitness_scores[i])
    return population[winner]


def roulette_selection(population, fitness_scores):
    # shift so the worst scores 0: works for GP's negative error as well as GA's positive counts
    worst = min(fitness_scores)
    weights = [score - worst for score in fitness_scores]
    if not any(weights):  # everyone equal, so pick uniformly
        return random.choice(population)
    return random.choices(population, weights=weights)[0]
