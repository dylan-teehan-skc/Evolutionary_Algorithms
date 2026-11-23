import copy
import math
import unittest
from pathlib import Path

import yaml

from src.climb.hang import (
    JOINTS,
    clamp_rate,
    hang_failures,
    joint_limits,
    reaches_next_rung,
)

CONFIG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config.yaml").read_text())


def variant(**changes):
    config = copy.deepcopy(CONFIG)
    for path, value in changes.items():
        section, key = path.split("__")
        config[section][key] = value
    return config


def stable_states():
    return [
        {
            "t": i / 60,
            "positions": [(0.0, 1.0)] * 5,
            "joint_angles": [0.0] * 4,
            "anchor_errors": [0.0, 0.0],
            "motor_forces": [30.0] * 4,
            "motor_rates": [0.0] * 4,
        }
        for i in range(301)
    ]


def broken(**changes):
    states = stable_states()
    states[-1].update(changes)
    return hang_failures(states, CONFIG)


class ReachabilityTests(unittest.TestCase):
    def test_design_geometry_is_reachable(self):
        self.assertTrue(reaches_next_rung(CONFIG))

    def test_rejects_too_large_pitch(self):
        self.assertFalse(reaches_next_rung(variant(ladder__rung_pitch=0.35)))

    def test_rejects_zero_elbow_flex(self):
        self.assertFalse(reaches_next_rung(variant(body__elbow_flex_limit=0)))

    def test_accepts_exactly_at_the_margin(self):
        config = variant(
            body__upper_arm={"length": 0.5, "mass": 1.0},
            body__forearm={"length": 0.5, "mass": 1.0},
            body__elbow_flex_limit=math.pi,
            ladder__rung_pitch=0.9,
            checks__reach_margin=0.9,
        )
        self.assertTrue(reaches_next_rung(config))


class JointTests(unittest.TestCase):
    def test_joint_order(self):
        self.assertEqual(
            JOINTS, ("right_shoulder", "right_elbow", "left_shoulder", "left_elbow")
        )

    def test_joint_limits_follow_joint_order(self):
        # angle 0 = arm straight up; each arm swings out and down its own side, barely across the body
        self.assertEqual(
            joint_limits(CONFIG["body"]),
            [(-2.9, 0.4), (0, 2.4), (-0.4, 2.9), (-2.4, 0)],
        )

    def test_clamp_rate(self):
        self.assertEqual(clamp_rate(10.0, 6.0), 6.0)
        self.assertEqual(clamp_rate(-10.0, 6.0), -6.0)
        self.assertEqual(clamp_rate(2.5, 6.0), 2.5)


class HangFailuresTests(unittest.TestCase):
    def test_stable_states_have_no_failures(self):
        self.assertEqual(hang_failures(stable_states(), CONFIG), {})

    def test_no_states(self):
        self.assertEqual(list(hang_failures([], CONFIG)), ["no_states"])

    def test_one_state_is_too_short(self):
        self.assertEqual(list(hang_failures(stable_states()[:1], CONFIG)), ["too_short"])

    def test_exactly_hang_seconds_is_accepted(self):
        states = [stable_states()[0], stable_states()[-1]]
        self.assertEqual(hang_failures(states, CONFIG), {})

    def test_non_finite_position(self):
        self.assertEqual(
            list(broken(positions=[(math.nan, 1.0)] + [(0.0, 1.0)] * 4)), ["non_finite"]
        )

    def test_angle_beyond_limit_plus_tol(self):
        self.assertEqual(
            list(broken(joint_angles=[0.4 + 0.06, 0.0, 0.0, 0.0])), ["angle_out_of_limits"]
        )

    def test_angle_at_limit_plus_tol_is_accepted(self):
        self.assertEqual(broken(joint_angles=[0.4 + 0.05, 0.0, 0.0, 0.0]), {})

    def test_anchor_error(self):
        self.assertEqual(list(broken(anchor_errors=[0.002, 0.0])), ["anchor_error"])

    def test_anchor_error_at_tol_is_accepted(self):
        self.assertEqual(broken(anchor_errors=[0.001, 0.0]), {})

    def test_displacement(self):
        moved = [(0.0, 1.0)] * 4 + [(0.0, 1.06)]
        self.assertEqual(list(broken(positions=moved)), ["displacement"])

    def test_displacement_at_max_is_accepted(self):
        moved = [(0.0, 1.0)] * 4 + [(0.05, 1.0)]  # x from 0.0 keeps the distance exact
        self.assertEqual(broken(positions=moved), {})

    def test_infinite_force(self):
        self.assertEqual(
            list(broken(motor_forces=[math.inf, 30.0, 30.0, 30.0])), ["motor_force_uncapped"]
        )

    def test_force_above_cap(self):
        self.assertEqual(
            list(broken(motor_forces=[30.1, 30.0, 30.0, 30.0])), ["motor_force_uncapped"]
        )

    def test_rate_over_cap(self):
        self.assertEqual(
            list(broken(motor_rates=[0.0, -6.1, 0.0, 0.0])), ["motor_rate_over_cap"]
        )

    def test_rate_at_cap_is_accepted(self):
        self.assertEqual(broken(motor_rates=[0.0, -6.0, 0.0, 0.0]), {})


if __name__ == "__main__":
    unittest.main()
