import sys
from pathlib import Path

import yaml

from src.climb.hang import JOINTS, hang_failures, max_static_gap, reaches_next_rung, rung_heights
from src.sim.stickman import simulate_hang

if __name__ == "__main__":
    config = yaml.safe_load(Path(__file__).with_name("config.yaml").read_text())
    reach = reaches_next_rung(config)
    print("REACH OK" if reach else "REACH FAILED")
    for name, override in config["ladders"].items():
        ys = rung_heights({**config["ladder"], **override})
        gaps = [b - a for a, b in zip(ys, ys[1:])]
        swing = next((k for k, g in enumerate(gaps) if g > max_static_gap(config)), None)
        need = f"must swing from gap {swing} (rung {swing} to {swing + 1})" if swing is not None else "no swing needed"
        print(f"{name}: gaps {gaps[0]:.2f}..{gaps[-1]:.2f} m, static reach {max_static_gap(config):.3f} m, {need}")

    states = simulate_hang(config)
    for joint, force in zip(JOINTS, states[0]["motor_forces"]):
        print(f"motor {joint} max_force={force} max_rate={config['body']['motor_max_rate']}")

    failures = hang_failures(states, config)
    if failures:
        for name, detail in failures.items():
            print(f"HANG FAILED {name}: {detail}")
    else:
        print(f"HANG STABLE: {len(states)} states over {states[-1]['t']:.1f} s")
    sys.exit(0 if reach and not failures else 1)
