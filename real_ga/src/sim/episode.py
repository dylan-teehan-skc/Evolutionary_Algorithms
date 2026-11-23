from src.climb.controller import control, decode, start
from src.sim.stickman import Stickman


def run_episode(config, genes, on_frame=None):
    # shell: steps the controller in the physics world and records the trace; stops early if both hands let go
    man = Stickman(config)
    p = decode(genes, config["body"])
    state = start()
    trace = []
    for _ in range(round(config["episode"]["seconds"] / config["body"]["dt"])):
        obs = man.observe()
        trace.append(obs)
        if on_frame:
            on_frame(man, obs)
        if obs["grips"] == [None, None]:
            if on_frame:  # video only: keep showing the fall; these frames are not in the scored trace
                for _ in range(round(config["video"]["fall_seconds"] / config["body"]["dt"])):
                    man.step([0.0] * 4)
                    on_frame(man, man.observe())
            break
        state, cmd = control(p, state, obs)
        for i in cmd["release"]:
            man.release(i)
        for i, min_rung in cmd["grip"]:
            man.try_grip(i, min_rung)
        man.step(cmd["rates"])
    return trace
