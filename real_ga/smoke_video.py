import os

os.environ["SDL_VIDEODRIVER"] = "dummy"  # headless: must be set before pygame is imported

from pathlib import Path

import imageio_ffmpeg
import pygame

WIDTH, HEIGHT = 320, 240  # even sizes, required by libx264 yuv420p
FRAMES = 10
FPS = 10
OUT = Path(__file__).with_name("results") / "smoke.mp4"

if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    pygame.font.init()
    font = pygame.font.Font(None, 36)
    writer = imageio_ffmpeg.write_frames(
        str(OUT), (WIDTH, HEIGHT), fps=FPS, codec="libx264", macro_block_size=2
    )
    writer.send(None)
    for i in range(FRAMES):
        surface = pygame.Surface((WIDTH, HEIGHT))
        surface.fill((20, 20, 30))
        surface.blit(font.render(f"LadderLab smoke {i + 1}/{FRAMES}", True, (240, 240, 240)), (10, 10))
        pygame.draw.circle(surface, (200, 80, 80), (30 + i * 28, HEIGHT // 2), 15)
        writer.send(pygame.image.tobytes(surface, "RGB"))
    writer.close()
    print(OUT)
    pygame.quit()
