from src.climb.hang import joint_limits

GENES = 23  # 4 poses x 4 joint targets, 4 phase timeouts, 3 servo gains
TIMEOUT = (0.2, 2.0)  # s
KP, KD, RATE_SCALE = (1.0, 20.0), (0.0, 2.0), (0.2, 1.0)
REACH = {0: 0, 2: 1}  # reach phase -> hand index (0 right, 1 left); phases 1 and 3 are pulls


def bounds(body):
    return joint_limits(body) * 4 + [TIMEOUT] * 4 + [KP, KD, RATE_SCALE]


def decode(genes, body):
    v = [(1 - g) * lo + g * hi for g, (lo, hi) in zip(genes, bounds(body))]  # exact at 0 and 1
    return {"poses": [v[i:i + 4] for i in range(0, 16, 4)], "timeouts": v[16:20],
            "kp": v[20], "kd": v[21], "rate_scale": v[22], "max_rate": body["motor_max_rate"]}


def servo(target, angle, speed, kp, kd, max_rate):
    rate = kp * (target - angle) - kd * speed
    return max(-max_rate, min(max_rate, rate))


def start():
    return {"phase": 0, "since": None, "from": None, "last": [0, 0]}


def control(p, state, obs):
    # pure: (params, state, observation) -> (new state, command)
    t, grips = obs["t"], obs["grips"]
    last = [g if g is not None else l for g, l in zip(grips, state["last"])]
    phase, since, frm = state["phase"], state["since"], state["from"]
    if since is None:
        since, frm = t, last[REACH[phase]] if phase in REACH else None

    hand = REACH.get(phase)
    done = t - since >= p["timeouts"][phase]
    if hand is not None and grips[hand] is not None and grips[hand] > frm:
        done = True
    if done:
        phase = (phase + 1) % 4
        since = t
        frm = last[REACH[phase]] if phase in REACH else None
        hand = REACH.get(phase)

    release, grip = [], []
    for i in (0, 1):
        if i == hand:
            other = grips[1 - i] is not None
            if grips[i] is not None and grips[i] <= frm and other:
                release.append(i)
            if grips[i] is None or i in release:
                grip.append((i, frm + 1))
        elif grips[i] is None:
            grip.append((i, last[i]))

    limit = p["max_rate"] * p["rate_scale"]
    rates = [servo(a, b, w, p["kp"], p["kd"], limit)
             for a, b, w in zip(p["poses"][phase], obs["joint_angles"], obs["joint_speeds"])]
    return ({"phase": phase, "since": since, "from": frm, "last": last},
            {"rates": rates, "release": release, "grip": grip})
