import unittest

from src.climb.fitness import score, verified_rungs

DT, PITCH, Y0 = 1 / 60, 0.25, 0.0


def trace(heights, grips):
    # heights and grips: one entry per frame; grips is (right, left) rung or None
    return [{"t": i * DT, "torso": (0.0, h), "grips": list(g)} for i, (h, g) in enumerate(zip(heights, grips))]


def hold(n, h, g):
    return [h] * n, [g] * n


def join(*parts):
    hs, gs = [], []
    for h, g in parts:
        hs += h
        gs += g
    return trace(hs, gs)


PASSIVE = join(hold(480, Y0, (0, 0)))
PARTIAL = join(hold(60, Y0, (0, 0)), hold(60, Y0 + 0.08, (1, 0)))
ONE_RUNG = join(hold(60, Y0, (0, 0)), hold(60, Y0 + PITCH, (1, 1)))
TWO_RUNGS = join(hold(60, Y0, (0, 0)), hold(60, Y0 + PITCH, (1, 1)), hold(60, Y0 + 2 * PITCH, (2, 2)))
FLING = join(hold(60, Y0, (0, 0)), hold(5, Y0 + 3 * PITCH, (3, None)), hold(60, Y0, (None, None)))
NO_GRIP_RISE = join(hold(60, Y0, (0, 0)), hold(60, Y0 + PITCH, (None, None)))


class FitnessTest(unittest.TestCase):
    def test_same_trace_same_score(self):
        self.assertEqual(score(ONE_RUNG, PITCH), score(ONE_RUNG, PITCH))

    def test_passive_scores_zero(self):
        self.assertEqual(score(PASSIVE, PITCH), 0.0)

    def test_partial_progress_beats_passive(self):
        self.assertGreater(score(PARTIAL, PITCH), score(PASSIVE, PITCH))

    def test_verified_rung_beats_any_partial_progress(self):
        self.assertEqual(verified_rungs(ONE_RUNG, PITCH), 1)
        self.assertLess(score(PARTIAL, PITCH), 1.0)
        self.assertGreaterEqual(score(ONE_RUNG, PITCH), 1.0)

    def test_each_rung_counted_once(self):
        self.assertEqual(verified_rungs(TWO_RUNGS, PITCH), 2)
        regrip = join(hold(60, Y0, (0, 0)), hold(60, PITCH, (1, 1)), hold(60, PITCH, (1, None)), hold(60, PITCH, (1, 1)))
        self.assertEqual(verified_rungs(regrip, PITCH), 1)

    def test_momentary_fling_earns_no_rung_credit(self):
        self.assertEqual(verified_rungs(FLING, PITCH), 0)
        self.assertLess(score(FLING, PITCH), 1.0)

    def test_rise_without_a_grip_earns_nothing(self):
        self.assertEqual(score(NO_GRIP_RISE, PITCH), 0.0)


if __name__ == "__main__":
    unittest.main()
