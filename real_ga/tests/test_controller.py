import math
import unittest
from pathlib import Path

import yaml

from src.climb.controller import GENES, bounds, control, decode, servo, start, swing

CONFIG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config.yaml").read_text())
BODY = CONFIG["body"]
DYNO = GENES - 1  # last gene: dyno on at >= 0.5


def genes(**at):
    g = [0.5] * GENES  # timeouts 1.1 s, release delay 0.75 s, catch delay 0.3 s
    # layout: 0-15 arm poses, 16-31 leg poses, 32 arm amp, 33 freq, 34-37 leg amps, 38-39 leg lags,
    # 40-43 timeouts, 44-46 servo, 47 release, 48 catch, 49 dyno
    g[DYNO] = 0.0
    for i, v in at.items():
        g[int(i[1:])] = v
    return g


def obs(t, grips=(0, 0), angles=(0.0,) * 8):
    return {"t": t, "grips": list(grips), "joint_angles": list(angles), "joint_speeds": [0.0] * 8}


def run(p, script):
    s, out = start(), []
    for t, grips in script:
        s, cmd = control(p, s, obs(t, grips))
        out.append((s["phase"], cmd))
    return out


class DecodeTest(unittest.TestCase):
    def test_there_are_50_genes(self):
        self.assertEqual(GENES, 50)
        self.assertEqual(len(bounds(BODY)), 50)

    def test_zeros_and_ones_land_exactly_on_the_bounds(self):
        table = bounds(BODY)
        flat = lambda p: p["flat"]
        self.assertEqual(flat(decode([0.0] * GENES, BODY)), [b[0] for b in table])
        self.assertEqual(flat(decode([1.0] * GENES, BODY)), [b[1] for b in table])

    def test_every_leg_joint_has_its_own_pose_gene(self):
        p = decode(genes(g16=0.0, g17=1.0, g18=1.0, g19=0.0), BODY)  # phase 0: right hip, right knee, left hip, left knee
        self.assertEqual(len(p["poses"]), 4)
        self.assertTrue(all(len(pose) == 8 for pose in p["poses"]))
        self.assertEqual(p["poses"][0][4:], [-1.2, 1.2, 1.2, -1.2])

    def test_dyno_is_on_from_one_half(self):
        self.assertFalse(decode(genes(), BODY)["dyno"])
        self.assertTrue(decode(genes(**{f"g{DYNO}": 0.5}), BODY)["dyno"])


class SwingTest(unittest.TestCase):
    def test_no_amplitude_no_swing(self):
        p = decode(genes(g32=0.0, g34=0.0, g35=0.0, g36=0.0, g37=0.0), BODY)
        self.assertEqual(swing(p, 0.37), [0.0] * 8)

    def test_shoulders_peak_at_the_arm_amplitude_together(self):
        p = decode(genes(g32=1.0), BODY)  # arm amplitude 1 rad
        quarter = 1 / (4 * p["freq"])
        out = swing(p, quarter)
        self.assertAlmostEqual(out[0], 1.0)
        self.assertAlmostEqual(out[2], 1.0)
        self.assertEqual((out[1], out[3]), (0.0, 0.0))

    def test_each_leg_swings_on_its_own_timing(self):
        # right leg lags a quarter turn, left leg does not: at the arms' peak the right hip is level, the left peaks
        p = decode(genes(g32=1.0, g34=1.0, g36=1.0, g38=0.25, g39=0.0), BODY)
        out = swing(p, 1 / (4 * p["freq"]))
        self.assertAlmostEqual(out[4], 0.0, places=9)
        self.assertAlmostEqual(out[6], 1.0, places=9)

    def test_each_leg_joint_has_its_own_amplitude(self):
        p = decode(genes(g34=0.0, g35=1.0, g36=0.5, g37=0.0, g38=0.0, g39=0.0), BODY)
        out = swing(p, 1 / (4 * p["freq"]))
        self.assertEqual([round(x, 9) for x in out[4:]], [0.0, 1.0, 0.5, 0.0])


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
        self.p = decode(genes(), BODY)

    def test_walks_reach_right_pull_reach_left_pull(self):
        script = [(0.0, (0, 0)), (0.5, (0, 0)), (0.8, (0, 0)), (1.0, (None, 0)), (1.2, (1, 0)), (1.3, (1, 0)),
                  (2.4, (1, 0)), (2.5, (1, 0)), (3.3, (1, None)), (3.7, (1, 1)), (4.9, (1, 1))]
        self.assertEqual([ph for ph, _ in run(self.p, script)], [0, 0, 0, 0, 1, 1, 2, 2, 2, 3, 0])

    def test_reaching_hand_is_released_only_after_the_release_delay(self):
        out = run(self.p, [(0.0, (0, 0)), (0.7, (0, 0)), (0.8, (0, 0))])
        self.assertEqual([cmd["release"] for _, cmd in out], [[], [], [0]])

    def test_no_release_without_the_other_hand_holding(self):
        out = run(self.p, [(0.0, (0, None)), (0.8, (0, None))])
        self.assertEqual(out[-1][1]["release"], [])

    def test_hand_stays_open_until_the_catch_delay(self):
        out = run(decode(genes(g40=1.0), BODY), [(0.0, (0, 0)), (0.8, (0, 0)), (1.0, (None, 0)), (1.15, (None, 0))])
        self.assertNotIn((0, 1), out[2][1]["grip"])
        self.assertIn((0, 1), out[3][1]["grip"])

    def test_dyno_lets_go_with_both_hands_and_both_catch(self):
        p = decode(genes(g40=1.0, **{f"g{DYNO}": 1.0}), BODY)  # reach timeout 2 s
        out = run(p, [(0.0, (0, 0)), (0.8, (0, 0)), (1.2, (None, None))])
        self.assertEqual(out[1][1]["release"], [0, 1])
        self.assertIn((0, 1), out[2][1]["grip"])
        self.assertIn((1, 0), out[2][1]["grip"])

    def test_phase_advances_on_timeout_without_a_grip(self):
        out = run(self.p, [(0.0, (0, 0)), (1.2, (None, 0))])
        self.assertEqual(out[-1][0], 1)

    def test_identical_observations_give_identical_commands(self):
        a = control(self.p, start(), obs(0.3, (None, 0), (0.1, 0.2, 0.3, -0.4, 0.1, 0.2, -0.1, -0.2)))
        b = control(self.p, start(), obs(0.3, (None, 0), (0.1, 0.2, 0.3, -0.4, 0.1, 0.2, -0.1, -0.2)))
        self.assertEqual(a, b)

    def test_rates_for_all_8_joints_are_bounded(self):
        _, cmd = control(self.p, start(), obs(0.0, (0, 0), (2.9, 0, -2.9, 0, 1.2, 0, -1.2, 0)))
        self.assertEqual(len(cmd["rates"]), 8)
        self.assertTrue(all(abs(r) <= BODY["motor_max_rate"] for r in cmd["rates"]))


if __name__ == "__main__":
    unittest.main()
