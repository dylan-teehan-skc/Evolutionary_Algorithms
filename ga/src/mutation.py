import random


def bit_flip_mutation(bits):
    mutated = bits[:]
    mutated[random.randrange(len(mutated))] ^= 1
    return mutated
