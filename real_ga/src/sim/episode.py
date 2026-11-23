import math

from src.climb.controller import control, decode, start
from src.climb.grip import fallen
from src.sim.stickman import Stickman


def run_episode(config, genes, on_frame=None):
    # shell: steps the controller in the physics world and records the trace; stops on a fall or a blow-up
    man = Stickman(config)
    p = decode(genes, config["body"])
    state = start()
    trace = []
    dt, flight = config["body"]["dt"], config["flight"]
    y0, free = man.observe()["torso"][1], 0.0
    for _ in range(round(config["episode"]["seconds"] / dt)):
        obs = man.observe()
        trace.append(obs)
        if not all(math.isfinite(v) for v in obs["torso"]):
            break
        if on_frame:
            on_frame(man, obs)
        free = free + dt if obs["grips"] == [None, None] else 0.0
        if fallen(free, y0 - obs["torso"][1], flight["max_seconds"], flight["max_drop"]):
            if on_frame:  # video only: keep showing the fall; these frames are not in the scored trace
                for _ in range(round(config["video"]["fall_seconds"] / dt)):
                    man.step([0.0] * len(man.motors))
                    on_frame(man, man.observe())
            break
        state, cmd = control(p, state, obs)
        for i in cmd["release"]:
            man.release(i)
        for i, min_rung in cmd["grip"]:
            man.try_grip(i, min_rung)
        man.step(cmd["rates"])
    return trace
