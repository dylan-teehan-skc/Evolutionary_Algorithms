import copy
import json
from pathlib import Path

import yaml

from src.climb.clips import improved_generations, next_version
from src.climb.controller import GENES
from src.climb.fitness import score
from src.climb.hang import rung_heights
from src.realga import evolve
from src.sim.episode import run_episode
from src.video.render import write_progression

if __name__ == "__main__":
    here = Path(__file__).parent
    base = yaml.safe_load((here / "config.yaml").read_text())
    out = here / "results"
    out.mkdir(exist_ok=True)

    segments = []
    for name, override in base["ladders"].items():  # L1 (even rungs) then L2 (widening gaps)
        config = copy.deepcopy(base)
        config["ladder"].update(override)
        rungs = rung_heights(config["ladder"])

        def evaluate(genes, config=config, rungs=rungs):
            return score(run_episode(config, genes), rungs)

        result = evolve(evaluate, GENES, config["ladder_ga"], seed=config["seed"])
        for h in result["history"]:
            print(f"{name} gen {h['gen']:3d}  best {h['best_score']:.3f}  evaluations {h['evaluations']}")
        (out / f"{name}_run.json").write_text(json.dumps(result, indent=1))

        clips = improved_generations(result["history"])
        for c in clips:  # replay integrity (VID-04): the stored genome must reproduce its stored fitness
            assert evaluate(c["best_genome"]) == c["best_score"], f"{name} replay mismatch at generation {c['gen']}"
        segments.append((name, config, clips, lambda g, frame, config=config: run_episode(config, g, on_frame=frame)))

    video = out / next_version("progression", [p.name for p in out.iterdir()])  # never overwrite an old video
    write_progression(video, base["video"], segments)
    print(f"{sum(len(s[2]) for s in segments)} clips -> {video}")
