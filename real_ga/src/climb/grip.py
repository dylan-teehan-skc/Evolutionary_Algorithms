def grip_target(tip, rung_ys, half_width, max_dist, min_rung=0):
    # index of the nearest rung at or above min_rung within max_dist of the hand tip, else None
    x, y = tip
    if abs(x) > half_width:
        return None
    best = None
    for i in range(min_rung, len(rung_ys)):
        d = abs(y - rung_ys[i])
        if d <= max_dist + 1e-12 and (best is None or d < abs(y - rung_ys[best])):
            best = i
    return best


def overloaded(impulse, dt, max_force):
    # pymunk reports the last step's impulse; impulse / dt is the force the grip carried
    return impulse / dt > max_force
