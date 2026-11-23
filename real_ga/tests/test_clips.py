import unittest

from src.climb.clips import improved_generations


def history(scores):
    return [{"gen": i, "best_score": s, "best_genome": [s]} for i, s in enumerate(scores)]


class ClipSelectionTest(unittest.TestCase):
    def test_generation_zero_plus_every_improvement_in_order(self):
        picked = improved_generations(history([0.1, 0.1, 0.4, 0.4, 0.4, 1.2, 1.3]))
        self.assertEqual([h["gen"] for h in picked], [0, 2, 5, 6])

    def test_no_improvement_gives_only_generation_zero(self):
        self.assertEqual([h["gen"] for h in improved_generations(history([0.5, 0.5]))], [0])

    def test_fitness_rises_from_clip_to_clip(self):
        scores = [h["best_score"] for h in improved_generations(history([0.0, 0.3, 0.2, 0.9]))]
        self.assertEqual(scores, sorted(scores))
        self.assertEqual(len(set(scores)), len(scores))


if __name__ == "__main__":
    unittest.main()
