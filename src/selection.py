import random


def tournament_selection(population, fitness_scores, tournament_size=3):
    contestants = random.sample(range(len(population)), tournament_size)
    winner = max(contestants, key=lambda i: fitness_scores[i])
    return population[winner]
