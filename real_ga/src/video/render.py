import os

os.environ["SDL_VIDEODRIVER"] = "dummy"  # headless: must be set before pygame is imported

import imageio_ffmpeg
import pygame

from src.climb.hang import rung_heights

WOOD, INK, JOINT, HELD, FREE = (140, 110, 80), (30, 40, 60), (210, 40, 40), (40, 170, 70), (90, 90, 90)


def write_progression(path, v, segments):
    # shell: each segment is (ladder name, config, clips, replay); replay(genes, on_frame) runs an episode.
    # every frame is drawn, nothing is decided here
    w, h, scale = v["width"], v["height"], v["pixels_per_m"]
    pygame.font.init()
    font, small = pygame.font.Font(None, 30), pygame.font.Font(None, 22)
    writer = imageio_ffmpeg.write_frames(str(path), (w, h), fps=v["fps"], codec="libx264", macro_block_size=2)
    writer.send(None)
    for name, config, clips, replay in segments:
        for clip in clips:
            last = []
            replay(clip["best_genome"], lambda man, obs: _frame(man, obs, name, clip, config, v, font, small, writer, last))
            for _ in range(v["fps"]):  # hold the final frame for a second between clips
                writer.send(last[0])
    writer.close()
    pygame.quit()


def _frame(man, obs, name, clip, config, v, font, small, writer, last):
    dt = config["body"]["dt"]
    if round(obs["t"] / dt) % max(1, round(1 / (v["fps"] * dt))):
        return
    w, h, scale = v["width"], v["height"], v["pixels_per_m"]
    top = obs["torso"][1] + 0.6 * h / scale  # camera follows the torso; drawing only

    def px(p):
        return int(w / 2 + p[0] * scale), int((top - p[1]) * scale)

    rungs, half = rung_heights(config["ladder"]), config["ladder"]["rung_half_width"]
    s = pygame.Surface((w, h))
    s.fill((245, 243, 236))
    for x in (-half, half):
        pygame.draw.line(s, WOOD, px((x, rungs[0] - 2)), px((x, rungs[-1] + 0.3)), 6)
    for k, y in enumerate(rungs):
        pygame.draw.line(s, WOOD, px((-half, y)), px((half, y)), 5)
        s.blit(small.render(str(k), True, WOOD), (px((half, y))[0] + 10, px((half, y))[1] - 8))
    for a, b in man.segments():
        pygame.draw.line(s, INK, px(a), px(b), 7)
    for j, end in man.joints():
        if end:  # shoulder and hip bars join the torso line to each limb
            pygame.draw.line(s, INK, px(j), px(end), 7)
    for j, _ in man.joints():
        pygame.draw.circle(s, JOINT, px(j), 7)
    centre, r = man.head()
    pygame.draw.circle(s, INK, px(centre), int(r * scale), 6)
    for tip, g in zip(obs["tips"], obs["grips"]):
        pygame.draw.circle(s, HELD if g is not None else FREE, px(tip), 8)
    label = f"{name}   Generation {clip['gen']}   fitness {clip['best_score']:.2f}   t={obs['t']:.1f}s"
    s.blit(font.render(label, True, (20, 20, 20)), (14, 12))
    data = pygame.image.tobytes(s, "RGB")
    last[:] = [data]
    writer.send(data)
