import json
from pathlib import Path

import yaml

from src.climb.clips import improved_generations
from src.climb.controller import GENES
from src.climb.fitness import score
from src.realga import evolve
from src.sim.episode import run_episode
from src.video.render import write_progression

if __name__ == "__main__":
    here = Path(__file__).parent
    config = yaml.safe_load((here / "config.yaml").read_text())
    pitch = config["ladder"]["rung_pitch"]
    out = here / "results"
    out.mkdir(exist_ok=True)

    def evaluate(genes):
        return score(run_episode(config, genes), pitch)

    result = evolve(evaluate, GENES, config["ladder_ga"], seed=config["seed"])
    for h in result["history"]:
        print(f"gen {h['gen']:3d}  best {h['best_score']:.3f}  evaluations {h['evaluations']}")
    (out / "ladder_run.json").write_text(json.dumps(result, indent=1))

    clips = improved_generations(result["history"])
    for c in clips:  # replay integrity (VID-04): the stored genome must reproduce its stored fitness
        assert evaluate(c["best_genome"]) == c["best_score"], f"replay mismatch at generation {c['gen']}"
    video = out / "progression.mp4"
    write_progression(video, config, clips, lambda g, frame: run_episode(config, g, on_frame=frame))
    print(f"{len(clips)} clips -> {video}")
