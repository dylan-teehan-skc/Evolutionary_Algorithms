import math
import unittest

from src.climb.fitness import score, verified_rungs

DT, PITCH, Y0 = 1 / 60, 0.25, 0.0
RUNGS = [k * PITCH for k in range(10)]  # even rung heights, rung 0 at the torso start height for simplicity
LOW = (0.0, -5.0)  # a hand tip far below every rung


def trace(heights, grips, tips=None):
    # heights and grips: one entry per frame; grips is (right, left) rung or None
    tips = tips or [(LOW, LOW)] * len(heights)
    return [{"t": i * DT, "torso": (0.0, h), "grips": list(g), "tips": list(p)}
            for i, (h, g, p) in enumerate(zip(heights, grips, tips))]


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
        self.assertEqual(score(ONE_RUNG, RUNGS), score(ONE_RUNG, RUNGS))

    def test_passive_scores_zero(self):
        self.assertEqual(score(PASSIVE, RUNGS), 0.0)

    def test_partial_progress_beats_passive(self):
        self.assertGreater(score(PARTIAL, RUNGS), score(PASSIVE, RUNGS))

    def test_verified_rung_beats_any_partial_progress(self):
        self.assertEqual(verified_rungs(ONE_RUNG, RUNGS), 1)
        self.assertLess(score(PARTIAL, RUNGS), 1.0)
        self.assertGreaterEqual(score(ONE_RUNG, RUNGS), 1.0)

    def test_each_rung_counted_once(self):
        self.assertEqual(verified_rungs(TWO_RUNGS, RUNGS), 2)
        regrip = join(hold(60, Y0, (0, 0)), hold(60, PITCH, (1, 1)), hold(60, PITCH, (1, None)), hold(60, PITCH, (1, 1)))
        self.assertEqual(verified_rungs(regrip, RUNGS), 1)

    def test_momentary_fling_earns_no_rung_credit(self):
        self.assertEqual(verified_rungs(FLING, RUNGS), 0)
        self.assertLess(score(FLING, RUNGS), 1.0)

    def test_rise_without_a_grip_earns_nothing(self):
        self.assertEqual(score(NO_GRIP_RISE, RUNGS), 0.0)


class WideningGapsTest(unittest.TestCase):
    WIDE = [0.0, 0.25, 0.6, 1.0]  # gaps 0.25, 0.35, 0.4

    def test_rung_needs_the_torso_raised_past_halfway_up_its_own_gap(self):
        just_short = join(hold(60, Y0, (0, 0)), hold(60, Y0 + 0.40, (2, 2)))  # halfway up 0.25..0.6 is 0.425
        enough = join(hold(60, Y0, (0, 0)), hold(60, Y0 + 0.45, (2, 2)))
        self.assertEqual(verified_rungs(just_short, self.WIDE), 1)
        self.assertEqual(verified_rungs(enough, self.WIDE), 2)

    def test_partial_progress_is_a_fraction_of_the_current_gap(self):
        part = join(hold(60, Y0, (0, 0)), hold(60, Y0 + 0.25 + 0.14, (1, 1)))  # 0.14 of the 0.35 gap = 40%
        self.assertAlmostEqual(score(part, self.WIDE), 1 + 0.5 * 0.4, places=6)


def one_hand(n, h, free_tip_y, held=0):
    # right hand holds rung `held`, the left hand is free with its tip at free_tip_y
    return trace([h] * n, [(held, None)] * n, [((0.0, RUNGS[held]), (0.0, free_tip_y))] * n)


class ReachBonusTest(unittest.TestCase):
    def test_free_hand_halfway_to_the_next_rung_earns_a_quarter_of_the_bonus_scale(self):
        self.assertAlmostEqual(score(one_hand(60, Y0, RUNGS[0] + PITCH / 2), RUNGS), 0.25 * 0.5, places=6)

    def test_bonus_needs_the_other_hand_holding(self):
        free = trace([Y0] * 60, [(None, None)] * 60, [((0, 1.0), (0, 1.0))] * 60)
        self.assertEqual(score(free, RUNGS), 0.0)

    def test_partial_credit_never_reaches_one_rung(self):
        best = one_hand(60, Y0 + 3 * PITCH, RUNGS[0] + 10.0)  # torso far up, free tip far up, still on rung 0
        self.assertEqual(verified_rungs(best, RUNGS), 0)
        self.assertLess(score(best, RUNGS), 1.0)

    def test_fling_earns_no_reach_bonus(self):
        self.assertLess(score(FLING, RUNGS), 0.5)


class NonFiniteTest(unittest.TestCase):
    def test_a_non_finite_trace_scores_zero(self):
        bad = join(hold(60, Y0, (0, 0)), hold(60, Y0 + PITCH, (1, 1)))
        bad[70]["torso"] = (0.0, math.nan)
        self.assertEqual(score(bad, RUNGS), 0.0)


if __name__ == "__main__":
    unittest.main()
