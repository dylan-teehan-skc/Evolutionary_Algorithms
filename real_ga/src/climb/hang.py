import math

JOINTS = ("right_shoulder", "right_elbow", "left_shoulder", "left_elbow")


def joint_limits(body):
    # (low, high) per joint in JOINTS order; a positive angle swings the far end toward -x
    out, inn, e = body["shoulder_out"], body["shoulder_in"], body["elbow_flex_limit"]
    return [(-out, inn), (0, e), (-inn, out), (-e, 0)]


def reaches_next_rung(config):
    # best case one-hand hang: gripping arm fully flexed, torso upright, free shoulder level
    # with the gripping shoulder; the free hand aims at the rung directly above it
    u = config["body"]["upper_arm"]["length"]
    f = config["body"]["forearm"]["length"]
    drop = math.sqrt(max(0.0, u * u + f * f + 2 * u * f * math.cos(config["body"]["elbow_flex_limit"])))
    return config["ladder"]["rung_pitch"] + drop <= config["checks"]["reach_margin"] * (u + f)


def clamp_rate(rate, max_rate):
    return max(-max_rate, min(max_rate, rate))


def hang_failures(states, config):
    # failure name -> one-line detail; empty means the hang is stable
    if not states:
        return {"no_states": "no states recorded"}
    checks, body = config["checks"], config["body"]
    span = states[-1]["t"] - states[0]["t"]
    if span < checks["hang_seconds"]:
        return {"too_short": f"{span:.3f} s < {checks['hang_seconds']} s"}

    values = [s["t"] for s in states]
    for s in states:
        values += [c for p in s["positions"] for c in p]
        values += s["joint_angles"] + s["anchor_errors"] + s["motor_rates"]
    if not all(math.isfinite(v) for v in values):
        return {"non_finite": "a time, position, angle, anchor error or rate is not finite"}

    failures = {}
    limits = joint_limits(body)
    tol = checks["angle_tol"]
    for s in states:
        for name, a, (lo, hi) in zip(JOINTS, s["joint_angles"], limits):
            if not lo - tol <= a <= hi + tol:
                failures.setdefault("angle_out_of_limits", f"{name} {a:.3f} rad at t={s['t']:.3f}")
        worst = max(s["anchor_errors"])
        if worst > checks["anchor_tol"]:
            failures.setdefault("anchor_error", f"{worst:.2e} m at t={s['t']:.3f}")
        far = max(math.dist(p, q) for p, q in zip(s["positions"], states[0]["positions"]))
        if far > checks["max_displacement"]:
            failures.setdefault("displacement", f"{far:.3f} m at t={s['t']:.3f}")
        if any(not f <= body["motor_max_force"] for f in s["motor_forces"]):
            failures.setdefault("motor_force_uncapped", f"{s['motor_forces']} at t={s['t']:.3f}")
        if any(abs(r) > body["motor_max_rate"] for r in s["motor_rates"]):
            failures.setdefault("motor_rate_over_cap", f"{s['motor_rates']} at t={s['t']:.3f}")
    return failures
