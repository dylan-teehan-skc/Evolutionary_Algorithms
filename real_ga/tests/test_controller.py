import unittest
from pathlib import Path

import yaml

from src.climb.controller import GENES, bounds, control, decode, servo, start

CONFIG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config.yaml").read_text())
BODY = CONFIG["body"]


def obs(t, grips=(0, 0), angles=(0.0,) * 4):
    return {"t": t, "grips": list(grips), "joint_angles": list(angles), "joint_speeds": [0.0] * 4}


class DecodeTest(unittest.TestCase):
    def test_there_are_23_genes(self):
        self.assertEqual(GENES, 23)
        self.assertEqual(len(bounds(BODY)), 23)

    def test_zeros_and_ones_land_on_the_bounds(self):
        table = bounds(BODY)
        lo, hi = decode([0.0] * 23, BODY), decode([1.0] * 23, BODY)
        flat = lambda p: [a for pose in p["poses"] for a in pose] + p["timeouts"] + [p["kp"], p["kd"], p["rate_scale"]]
        self.assertEqual(flat(lo), [b[0] for b in table])
        self.assertEqual(flat(hi), [b[1] for b in table])

    def test_decoded_values_stay_inside_the_bounds(self):
        p = decode([0.37] * 23, BODY)
        self.assertEqual(len(p["poses"]), 4)
        self.assertTrue(all(len(pose) == 4 for pose in p["poses"]))
        self.assertEqual(len(p["timeouts"]), 4)
        flat = [a for pose in p["poses"] for a in pose] + p["timeouts"] + [p["kp"], p["kd"], p["rate_scale"]]
        self.assertTrue(all(lo <= v <= hi for v, (lo, hi) in zip(flat, bounds(BODY))))


class ServoTest(unittest.TestCase):
    def test_zero_at_target_with_zero_speed(self):
        self.assertEqual(servo(1.0, 1.0, 0.0, kp=5, kd=0.5, max_rate=6), 0.0)

    def test_moves_toward_the_target(self):
        self.assertGreater(servo(1.0, 0.5, 0.0, kp=5, kd=0.5, max_rate=6), 0)
        self.assertLess(servo(-1.0, 0.5, 0.0, kp=5, kd=0.5, max_rate=6), 0)

    def test_never_exceeds_max_rate(self):
        self.assertEqual(servo(3.0, -3.0, 0.0, kp=50, kd=0, max_rate=6), 6)
        self.assertEqual(servo(-3.0, 3.0, 0.0, kp=50, kd=0, max_rate=6), -6)


class ControllerTest(unittest.TestCase):
    def setUp(self):
        self.p = decode([0.5] * 23, BODY)  # timeouts 1.1 s each

    def test_walks_reach_right_pull_reach_left_pull(self):
        s, phases = start(), []
        script = [(0.0, (0, 0)), (0.1, (None, 0)), (0.5, (1, 0)), (0.6, (1, 0)), (2.0, (1, 0)),
                  (2.1, (1, None)), (2.5, (1, 1)), (3.0, (1, 1)), (4.0, (1, 1)), (4.1, (None, 1))]
        for t, grips in script:
            s, _ = control(self.p, s, obs(t, grips))
            phases.append(s["phase"])
        self.assertEqual(phases, [0, 0, 1, 1, 2, 2, 3, 3, 0, 0])

    def test_reach_releases_the_reaching_hand_only_while_the_other_holds(self):
        _, cmd = control(self.p, start(), obs(0.0, (0, 0)))
        self.assertEqual(cmd["release"], [0])
        _, cmd = control(self.p, start(), obs(0.0, (0, None)))
        self.assertEqual(cmd["release"], [])

    def test_reaching_hand_asks_for_a_higher_rung(self):
        s, _ = control(self.p, start(), obs(0.0, (0, 0)))
        _, cmd = control(self.p, s, obs(0.1, (None, 0)))
        self.assertIn((0, 1), cmd["grip"])

    def test_phase_advances_on_timeout_without_a_grip(self):
        s, _ = control(self.p, start(), obs(0.0, (0, 0)))
        s, _ = control(self.p, s, obs(1.2, (None, 0)))
        self.assertEqual(s["phase"], 1)

    def test_identical_observations_give_identical_commands(self):
        a = control(self.p, start(), obs(0.3, (None, 0), (0.1, 0.2, 0.3, -0.4)))
        b = control(self.p, start(), obs(0.3, (None, 0), (0.1, 0.2, 0.3, -0.4)))
        self.assertEqual(a, b)

    def test_rates_are_bounded(self):
        _, cmd = control(self.p, start(), obs(0.0, (0, 0), (2.6, 0, -2.6, 0)))
        self.assertEqual(len(cmd["rates"]), 4)
        self.assertTrue(all(abs(r) <= BODY["motor_max_rate"] for r in cmd["rates"]))


if __name__ == "__main__":
    unittest.main()
