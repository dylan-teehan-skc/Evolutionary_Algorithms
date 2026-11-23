import os

os.environ["SDL_VIDEODRIVER"] = "dummy"  # headless: must be set before pygame is imported

import imageio_ffmpeg
import pygame

from src.sim.stickman import rung_ys


def write_progression(path, config, clips, replay):
    # shell: replay(genes, on_frame) runs an episode; every frame is drawn, nothing is decided here
    v = config["video"]
    w, h, scale = v["width"], v["height"], v["pixels_per_m"]
    every = max(1, round(1 / (v["fps"] * config["body"]["dt"])))
    rungs, half = rung_ys(config), config["ladder"]["rung_half_width"]
    view = {"top": 0.0}

    def px(p):
        return int(w / 2 + p[0] * scale), int((view["top"] - p[1]) * scale)

    pygame.font.init()
    font = pygame.font.Font(None, 30)
    small = pygame.font.Font(None, 22)
    writer = imageio_ffmpeg.write_frames(str(path), (w, h), fps=v["fps"], codec="libx264", macro_block_size=2)
    writer.send(None)

    for clip in clips:
        last = []

        def frame(man, obs):
            if round(obs["t"] / config["body"]["dt"]) % every:
                return
            view["top"] = obs["torso"][1] + 0.6 * h / scale  # camera follows the torso; drawing only
            s = pygame.Surface((w, h))
            s.fill((245, 243, 236))
            for x in (-half, half):
                pygame.draw.line(s, (140, 110, 80), px((x, rungs[0] - 2)), px((x, rungs[-1] + 0.3)), 6)
            for k, y in enumerate(rungs):
                pygame.draw.line(s, (140, 110, 80), px((-half, y)), px((half, y)), 5)
                s.blit(small.render(str(k), True, (140, 110, 80)), (px((half, y))[0] + 10, px((half, y))[1] - 8))
            for a, b in man.segments():
                pygame.draw.line(s, (30, 40, 60), px(a), px(b), 7)
            for j, end in man.joints():
                if end:  # shoulder and hip bars join the torso line to each limb
                    pygame.draw.line(s, (30, 40, 60), px(j), px(end), 7)
            for j, _ in man.joints():
                pygame.draw.circle(s, (210, 40, 40), px(j), 7)
            centre, r = man.head()
            pygame.draw.circle(s, (30, 40, 60), px(centre), int(r * scale), 6)
            for tip, g in zip(obs["tips"], obs["grips"]):
                pygame.draw.circle(s, (40, 170, 70) if g is not None else (90, 90, 90), px(tip), 8)
            label = f"Generation {clip['gen']}   fitness {clip['best_score']:.2f}   t={obs['t']:.1f}s"
            s.blit(font.render(label, True, (20, 20, 20)), (14, 12))
            data = pygame.image.tobytes(s, "RGB")
            last[:] = [data]
            writer.send(data)

        replay(clip["best_genome"], frame)
        for _ in range(v["fps"]):  # hold the final frame for a second between clips
            writer.send(last[0])
    writer.close()
    pygame.quit()
