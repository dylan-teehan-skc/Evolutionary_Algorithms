import math

from src.climb.hang import joint_limits

# 16 arm pose + 16 leg pose + 8 swing + 4 timeouts + 3 servo + 3 grip timing genes
GENES = 50
TIMEOUT = (0.2, 2.0)  # s
KP, KD, RATE_SCALE = (1.0, 20.0), (0.0, 2.0), (0.2, 1.0)
AMP, FREQ, LAG = (0.0, 1.0), (0.3, 2.0), (0.0, 2 * math.pi)  # rad, Hz, rad
RELEASE, CATCH, DYNO = (0.0, 1.5), (0.0, 0.6), (0.0, 1.0)  # s after reach starts, s after release, flag
REACH = {0: 0, 2: 1}  # reach phase -> hand index (0 right, 1 left); phases 1 and 3 are pulls


def bounds(body):
    limits = joint_limits(body)
    return (limits[:4] * 4 + limits[4:] * 4 + [AMP, FREQ] + [AMP] * 4 + [LAG] * 2 + [TIMEOUT] * 4
            + [KP, KD, RATE_SCALE] + [RELEASE, CATCH, DYNO])


def decode(genes, body):
    v = [(1 - g) * lo + g * hi for g, (lo, hi) in zip(genes, bounds(body))]  # exact at 0 and 1
    # each phase: 4 arm targets, then its own right hip, right knee, left hip and left knee targets
    poses = [v[4 * i:4 * i + 4] + v[16 + 4 * i:20 + 4 * i] for i in range(4)]
    return {"flat": v, "poses": poses, "arm_amp": v[32], "freq": v[33], "leg_amps": v[34:38], "leg_lags": v[38:40],
            "timeouts": v[40:44], "kp": v[44], "kd": v[45], "rate_scale": v[46],
            "release": v[47], "catch": v[48], "dyno": genes[49] >= 0.5, "max_rate": body["motor_max_rate"]}


def swing(p, t):
    # oscillation added to the pose: both shoulders together (the body sways); each leg on its own timing,
    # each hip and knee with its own amplitude
    w = 2 * math.pi * p["freq"] * t
    a = p["arm_amp"] * math.sin(w)
    right, left = math.sin(w - p["leg_lags"][0]), math.sin(w - p["leg_lags"][1])
    rh, rk, lh, lk = p["leg_amps"]
    return [a, 0.0, a, 0.0, rh * right, rk * right, lh * left, lk * left]


def servo(target, angle, speed, kp, kd, max_rate):
    rate = kp * (target - angle) - kd * speed
    return max(-max_rate, min(max_rate, rate))


def start():
    return {"phase": 0, "since": None, "from": None, "last": [0, 0], "released": None}


def control(p, state, obs):
    # pure: (params, state, observation) -> (new state, command)
    t, grips = obs["t"], obs["grips"]
    last = [g if g is not None else l for g, l in zip(grips, state["last"])]
    phase, since, frm, released = state["phase"], state["since"], state["from"], state["released"]
    if since is None:
        since, frm = t, last[REACH[phase]] if phase in REACH else None

    hand = REACH.get(phase)
    done = t - since >= p["timeouts"][phase]
    if hand is not None and grips[hand] is not None and grips[hand] > frm:
        done = True
    if done:
        phase, since, released = (phase + 1) % 4, t, None
        frm = last[REACH[phase]] if phase in REACH else None
        hand = REACH.get(phase)

    release = []
    if hand is not None and released is None and t - since >= p["release"]:
        other = 1 - hand
        if grips[hand] is None:
            released = t  # already free: start the catch clock now
        elif grips[hand] <= frm and (grips[other] is not None or p["dyno"]):
            release = [hand] + ([other] if p["dyno"] and grips[other] is not None else [])
            released = t
    closed = released is not None and t - released >= p["catch"]

    grip = []
    for i in (0, 1):
        if grips[i] is not None and i not in release:
            continue
        if i == hand:
            if closed:
                grip.append((i, frm + 1))
        elif hand is not None and p["dyno"] and released is not None:
            if closed:
                grip.append((i, last[i]))
        else:
            grip.append((i, last[i]))

    target = [a + b for a, b in zip(p["poses"][phase], swing(p, t))]
    limit = p["max_rate"] * p["rate_scale"]
    rates = [servo(a, b, w, p["kp"], p["kd"], limit)
             for a, b, w in zip(target, obs["joint_angles"], obs["joint_speeds"])]
    return ({"phase": phase, "since": since, "from": frm, "last": last, "released": released},
            {"rates": rates, "release": release, "grip": grip})
