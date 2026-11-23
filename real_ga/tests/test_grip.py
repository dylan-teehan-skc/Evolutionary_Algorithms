import unittest

from src.climb.grip import grip_target, overloaded

RUNGS = [1.5, 1.75, 2.0]


class GripTargetTest(unittest.TestCase):
    def test_tip_on_a_rung_grips_that_rung(self):
        self.assertEqual(grip_target((0.1, 1.75), RUNGS, half_width=0.3, max_dist=0.03), 1)

    def test_tip_within_distance_grips_nearest_rung(self):
        self.assertEqual(grip_target((0.1, 1.98), RUNGS, half_width=0.3, max_dist=0.03), 2)

    def test_tip_beyond_distance_is_refused(self):
        self.assertIsNone(grip_target((0.1, 1.85), RUNGS, half_width=0.3, max_dist=0.03))

    def test_tip_outside_the_ladder_width_is_refused(self):
        self.assertIsNone(grip_target((0.5, 1.75), RUNGS, half_width=0.3, max_dist=0.03))

    def test_rungs_below_min_rung_are_ignored(self):
        self.assertIsNone(grip_target((0.1, 1.5), RUNGS, half_width=0.3, max_dist=0.03, min_rung=1))

    def test_distance_exactly_at_limit_grips(self):
        self.assertEqual(grip_target((0.0, 1.5 + 0.03), RUNGS, half_width=0.3, max_dist=0.03), 0)


class OverloadTest(unittest.TestCase):
    def test_force_above_limit_overloads(self):
        self.assertTrue(overloaded(impulse=0.5, dt=0.001, max_force=400.0))

    def test_force_at_or_below_limit_holds(self):
        self.assertFalse(overloaded(impulse=0.4, dt=0.001, max_force=400.0))
        self.assertFalse(overloaded(impulse=0.0, dt=0.001, max_force=400.0))


if __name__ == "__main__":
    unittest.main()
