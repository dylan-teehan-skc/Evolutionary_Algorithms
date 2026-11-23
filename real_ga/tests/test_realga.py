import random
import unittest

from src.realga import blend, evolve, initialise, mutate, random_search, tournament

SETTINGS = {"population_size": 10, "elites": 2, "max_evaluations": 50,
            "mutation_prob": 0.2, "mutation_sigma": 0.1, "tournament_size": 3}


def sphere(g):
    return -sum((x - 0.7) ** 2 for x in g)


class Counter:
    def __init__(self):
        self.calls, self.seen = 0, []

    def __call__(self, g):
        self.calls += 1
        self.seen.append(tuple(g))
        return sphere(g)


class OperatorTest(unittest.TestCase):
    def test_initialise_draws_genes_in_unit_interval(self):
        pop = initialise(random.Random(1), 20, 23)
        self.assertEqual(len(pop), 20)
        self.assertTrue(all(len(g) == 23 and all(0 <= x <= 1 for x in g) for g in pop))

    def test_tournament_returns_best_contestant_when_all_compete(self):
        pop = [[0.1], [0.9], [0.5]]
        self.assertEqual(tournament(random.Random(1), pop, [1.0, 3.0, 2.0], size=3, replace=False), [0.9])

    def test_blend_children_are_convex_combinations(self):
        a, b = [0.0, 0.2, 1.0], [1.0, 0.6, 0.0]
        for c in blend(random.Random(3), a, b):
            self.assertTrue(all(min(x, y) <= z <= max(x, y) for x, y, z in zip(a, b, c)))

    def test_mutation_clips_to_unit_interval(self):
        out = mutate(random.Random(2), [0.0, 1.0] * 50, prob=1.0, sigma=5.0)
        self.assertTrue(all(0 <= x <= 1 for x in out))
        self.assertNotEqual(out, [0.0, 1.0] * 50)


class EvolveTest(unittest.TestCase):
    def test_budget_counts_every_call_and_stops_at_max(self):
        f = Counter()
        result = evolve(f, 5, SETTINGS, seed=4)
        self.assertEqual(f.calls, 50)
        self.assertEqual(result["evaluations"], 50)

    def test_last_generation_may_be_partial_so_the_budget_is_spent_exactly(self):
        f = Counter()
        result = evolve(f, 5, dict(SETTINGS, max_evaluations=55), seed=4)
        self.assertEqual(f.calls, 55)

    def test_never_re_evaluates_a_scored_genome(self):
        f = Counter()
        evolve(f, 5, SETTINGS, seed=4)
        self.assertEqual(len(f.seen), len(set(f.seen)))

    def test_elites_survive_and_best_never_drops(self):
        history = evolve(Counter(), 5, SETTINGS, seed=4)["history"]
        scores = [h["best_score"] for h in history]
        self.assertEqual(scores, sorted(scores))
        self.assertEqual(history[-1]["evaluations"], 50)

    def test_result_reports_best_ever(self):
        r = evolve(Counter(), 5, SETTINGS, seed=4)
        self.assertEqual(r["best_score"], sphere(r["best_genome"]))
        self.assertEqual(r["best_score"], r["history"][-1]["best_score"])

    def test_same_seed_same_run(self):
        self.assertEqual(evolve(Counter(), 5, SETTINGS, seed=9), evolve(Counter(), 5, SETTINGS, seed=9))

    def test_ga_improves_on_its_first_generation(self):
        h = evolve(Counter(), 5, dict(SETTINGS, max_evaluations=400), seed=1)["history"]
        self.assertGreater(h[-1]["best_score"], h[0]["best_score"])


class RandomSearchTest(unittest.TestCase):
    def test_same_budget_and_result_shape(self):
        f = Counter()
        r = random_search(f, 5, SETTINGS, seed=4)
        self.assertEqual(f.calls, 50)
        self.assertEqual(set(r), set(evolve(Counter(), 5, SETTINGS, seed=4)))
        self.assertEqual(len(r["history"]), 6)


if __name__ == "__main__":
    unittest.main()
