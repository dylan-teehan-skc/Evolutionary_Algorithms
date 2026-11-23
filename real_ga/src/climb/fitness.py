HOLD = 0.25  # s a rise must be held with a valid grip to count (FIT-02, FIT-04)
SHAPING = 0.5  # partial progress is worth less than one verified rung


def _windows(trace):
    # every held window: (lowest gripped rung across it, lowest torso height across it)
    out = []
    for i, first in enumerate(trace):
        level, low = 99, first["torso"][1]
        for f in trace[i:]:
            held = [g for g in f["grips"] if g is not None]
            if not held:
                break
            level, low = min(level, max(held)), min(low, f["torso"][1])
            if f["t"] - first["t"] >= HOLD:
                out.append((level, low))
                break
    return out


def verified_rungs(trace, pitch):
    # highest k with a hand on rung >= k and the torso held at least (k - 0.5) pitches up, for HOLD seconds
    y0 = trace[0]["torso"][1]
    best = 0
    for level, low in _windows(trace):
        k = min(level, int((low - y0) / pitch + 0.5))
        best = max(best, k)
    return best


def score(trace, pitch):
    # pure: verified rungs, plus a held-height bonus below one rung; passive or fling-only scores 0
    y0 = trace[0]["torso"][1]
    rungs = verified_rungs(trace, pitch)
    rise = max([(low - y0) / pitch for _, low in _windows(trace)] + [0.0])
    return rungs + SHAPING * min(1.0, max(0.0, rise - rungs))
