import pymunk

from src.climb.grip import grip_target, overloaded
from src.climb.hang import JOINTS, clamp_rate, joint_limits

SIDES = ("right", "left")


def rung_ys(config):
    ladder = config["ladder"]
    return [ladder["first_rung_y"] + k * ladder["rung_pitch"] for k in range(ladder["rung_count"])]


class Stickman:
    # humble shell: builds, steps and reads pymunk; every decision is a pure function in src.climb
    def __init__(self, config):
        self.config = config
        body, ladder = config["body"], config["ladder"]
        torso_len = body["torso"]["length"]
        upper, fore = body["upper_arm"]["length"], body["forearm"]["length"]
        half = body["shoulder_half_width"]
        self.fore = fore
        self.rungs = rung_ys(config)

        space = pymunk.Space()
        space.gravity = (0, body["gravity"])
        space.iterations = body["solver_iterations"]
        self.space = space

        def make(spec, centre):
            mass, length = spec["mass"], spec["length"]
            moment = pymunk.moment_for_segment(mass, (0, -length / 2), (0, length / 2), 0.0)
            b = pymunk.Body(mass, moment)
            b.position = centre
            space.add(b)  # no shapes: rungs are bars behind the body (D-03)
            self.half[b] = length / 2
            return b

        self.half = {}

        shoulder_y = ladder["first_rung_y"] - (upper + fore)
        self.torso = make(body["torso"], (0, shoulder_y - torso_len / 2))
        self.parts = [self.torso]
        self.arms, self.hands, self.motors = [], [], []
        limits = iter(joint_limits(body))
        for side in (1, -1):  # right then left, matching JOINTS
            x = side * half
            arm = make(body["upper_arm"], (x, shoulder_y + upper / 2))
            hand = make(body["forearm"], (x, shoulder_y + upper + fore / 2))
            self.parts += [arm, hand]
            self.arms.append((self.torso, arm, hand))
            self.hands.append(hand)
            space.add(
                pymunk.PivotJoint(self.torso, arm, (x, torso_len / 2), (0, -upper / 2)),
                pymunk.PivotJoint(arm, hand, (0, upper / 2), (0, -fore / 2)),
            )
            for parent, child in ((self.torso, arm), (arm, hand)):
                lo, hi = next(limits)
                motor = pymunk.SimpleMotor(parent, child, 0.0)
                motor.max_force = body["motor_max_force"]
                space.add(pymunk.RotaryLimitJoint(parent, child, lo, hi), motor)
                self.motors.append(motor)

        # passive legs: hips and knees are limited, spring-damped joints with no motors
        hip_y = shoulder_y - torso_len
        for side in (1, -1):
            x = side * body["hip_half_width"]
            th, sh = body["thigh"]["length"], body["shin"]["length"]
            thigh = make(body["thigh"], (x, hip_y - th / 2))
            shin = make(body["shin"], (x, hip_y - th - sh / 2))
            self.parts += [thigh, shin]
            for parent, child, anchor_a, anchor_b, lo, hi in (
                (self.torso, thigh, (x, -torso_len / 2), (0, th / 2), -body["hip_limit"], body["hip_limit"]),
                (thigh, shin, (0, -th / 2), (0, sh / 2), -body["knee_limit"] * (side < 0), body["knee_limit"] * (side > 0)),
            ):
                space.add(
                    pymunk.PivotJoint(parent, child, anchor_a, anchor_b),
                    pymunk.RotaryLimitJoint(parent, child, lo, hi),
                    pymunk.DampedRotarySpring(parent, child, 0.0, body["leg_stiffness"], body["leg_damping"]),
                )

        self.grips = [None, None]  # (PivotJoint, rung index, pin) per side
        self.last_rung = [0, 0]
        self.ticks = 0
        for i in range(2):
            self.try_grip(i, min_rung=0)

    def tip(self, i):
        return tuple(self.hands[i].local_to_world((0, self.fore / 2)))

    def try_grip(self, i, min_rung):
        # returns "grip" or "refused"; the pivot goes exactly at the tip, so nothing moves
        if self.grips[i] is not None:
            return "refused"
        g = self.config["grip"]
        k = grip_target(self.tip(i), self.rungs, self.config["ladder"]["rung_half_width"], g["max_dist"], min_rung)
        if k is None:
            return "refused"
        pin = self.tip(i)
        joint = pymunk.PivotJoint(self.space.static_body, self.hands[i], pin, (0, self.fore / 2))
        self.space.add(joint)
        self.grips[i] = (joint, k, pin)
        self.last_rung[i] = k
        return "grip"

    def release(self, i):
        if self.grips[i] is None:
            return None
        self.space.remove(self.grips[i][0])
        self.grips[i] = None
        return "release"

    def step(self, rates):
        # rates: one per joint in JOINTS order, positive raises the joint angle; returns break events
        body = self.config["body"]
        for m, r in zip(self.motors, rates):
            m.rate = -clamp_rate(r, body["motor_max_rate"])
        events = []
        h = body["dt"] / body["substeps"]
        for _ in range(body["substeps"]):
            self.space.step(h)
            for i, g in enumerate(self.grips):
                if g is not None and overloaded(g[0].impulse, h, self.config["grip"]["max_force"]):
                    self.space.remove(g[0])
                    self.grips[i] = None
                    events.append((SIDES[i], "break"))
        self.ticks += 1
        return events

    def observe(self):
        angles, speeds = [], []
        for t_, a_, h_ in self.arms:
            angles += [a_.angle - t_.angle, h_.angle - a_.angle]
            speeds += [a_.angular_velocity - t_.angular_velocity, h_.angular_velocity - a_.angular_velocity]
        return {
            "t": self.ticks * self.config["body"]["dt"],
            "torso": tuple(self.torso.position),
            "joint_angles": angles,
            "joint_speeds": speeds,
            "grips": [None if g is None else g[1] for g in self.grips],
            "tips": [self.tip(0), self.tip(1)],
        }

    def segments(self):
        # world endpoints of every part, for rendering
        return [(tuple(b.local_to_world((0, -self.half[b]))), tuple(b.local_to_world((0, self.half[b])))) for b in self.parts]

    def joints(self):
        # (world position, torso end it hangs off or None) for every body-to-body pivot, for rendering
        out = []
        for j in self.space.constraints:
            if isinstance(j, pymunk.PivotJoint) and j.a is not self.space.static_body:
                end = None
                if j.a is self.torso:
                    end = tuple(self.torso.local_to_world((0, self.half[self.torso] * (1 if j.anchor_a.y > 0 else -1))))
                out.append((tuple(j.a.local_to_world(j.anchor_a)), end))
        return out

    def head(self):
        # head centre, drawn on top of the torso (its mass is part of the torso)
        r = self.config["body"]["head_radius"]
        return tuple(self.torso.local_to_world((0, self.half[self.torso] + r))), r


def simulate_hang(config):
    # builds, steps and reads only; judging the states is src.climb.hang.hang_failures
    man = Stickman(config)
    pins = [g[2] for g in man.grips]

    def record():
        obs = man.observe()
        return {
            "t": obs["t"],
            "positions": [tuple(p.position) for p in man.parts],
            "joint_angles": obs["joint_angles"],
            "anchor_errors": [pymunk.Vec2d(*man.tip(i)).get_distance(p) for i, p in enumerate(pins)],
            "motor_forces": [m.max_force for m in man.motors],
            "motor_rates": [-m.rate for m in man.motors],
        }

    states = [record()]
    for _ in range(round(config["checks"]["hang_seconds"] / config["body"]["dt"])):
        man.step([0.0] * len(JOINTS))
        states.append(record())
    return states
