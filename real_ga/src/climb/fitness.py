HOLD = 0.25  # s a rise must be held with a valid grip to count (FIT-02, FIT-04)
import math

SHAPING = 0.5  # held torso height between rungs; with REACH_BONUS, partial credit stays below one rung
REACH_BONUS = 0.25  # how far the free hand gets toward the next rung while the other hand holds


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


def _progress(rise, rungs):
    # torso rise as a fractional rung index: k means risen exactly as high as rung k is above rung 0
    off = [r - rungs[0] for r in rungs]
    if rise <= 0:
        return 0.0
    for k in range(len(off) - 1):
        if rise < off[k + 1]:
            return k + (rise - off[k]) / (off[k + 1] - off[k])
    return float(len(off) - 1)


def verified_rungs(trace, rungs):
    # highest k with a hand on rung >= k and the torso held over halfway up gap k, for HOLD seconds
    y0 = trace[0]["torso"][1]
    best = 0
    for level, low in _windows(trace):
        best = max(best, min(level, int(_progress(low - y0, rungs) + 0.5)))
    return best


def _reach(trace, rungs, frontier):
    # best fraction of the gap above the held rung that the free hand's tip reaches, one hand holding
    best = 0.0
    for f in trace:
        held = [g for g in f["grips"] if g is not None]
        if len(held) != 1 or held[0] < frontier or held[0] + 1 >= len(rungs):
            continue
        g = held[0]
        tip_y = f["tips"][f["grips"].index(None)][1]
        best = max(best, min(1.0, max(0.0, (tip_y - rungs[g]) / (rungs[g + 1] - rungs[g]))))
    return best


def _finite(trace):
    return all(math.isfinite(v) for f in trace for v in (*f["torso"], *(c for p in f.get("tips", []) for c in p)))


def score(trace, rungs):
    # pure: verified rungs, plus partial credit below one rung; passive, fling-only or non-finite scores 0
    if not _finite(trace):
        return 0.0
    y0 = trace[0]["torso"][1]
    done = verified_rungs(trace, rungs)
    rise = max([_progress(low - y0, rungs) for _, low in _windows(trace)] + [0.0])
    return done + SHAPING * min(1.0, max(0.0, rise - done)) + REACH_BONUS * _reach(trace, rungs, done)
