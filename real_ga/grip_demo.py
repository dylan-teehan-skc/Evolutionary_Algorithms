import copy
from pathlib import Path

import yaml

from src.sim.stickman import SIDES, Stickman

config = yaml.safe_load(Path(__file__).with_name("config.yaml").read_text())
log = []


def run(man, seconds, rates=(0.0, 0.0, 0.0, 0.0)):
    for _ in range(round(seconds / config["body"]["dt"])):
        log.extend(man.step(list(rates)))


man = Stickman(config)
log += [("right", "grip"), ("left", "grip")]
run(man, 2.0)  # normal load: both grips should hold
log.append(("left", man.release(1)))
before = [tuple(p.position) for p in man.parts]
log.append(("left", man.try_grip(1, min_rung=0)))  # tip still on the rung: grips without moving anything
moved = max(abs(a - b) for p, q in zip(before, [tuple(p.position) for p in man.parts]) for a, b in zip(p, q))
print(f"max body movement at grip: {moved:.2e} m")
log.append(("left", man.release(1)))
run(man, 0.5, rates=(0.0, 0.0, 3.0, 0.0))  # swing the free left arm away from the rung
log.append(("left", man.try_grip(1, min_rung=0)))  # too far: refused

heavy = copy.deepcopy(config)
heavy["grip"]["max_force"] = 10.0  # below the ~25 N each grip carries
weak = Stickman(heavy)
run(weak, 0.1)

for side, event in log:
    print(f"{side:5s} {event}")
