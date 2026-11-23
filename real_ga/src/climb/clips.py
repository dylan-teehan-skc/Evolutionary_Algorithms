def improved_generations(history):
    # generation 0 plus every generation whose best score beat all earlier ones (VID-02)
    picked = []
    for h in history:
        if not picked or h["best_score"] > picked[-1]["best_score"]:
            picked.append(h)
    return picked


def next_version(stem, existing):
    # first free name of stem.mp4, stem_v2.mp4, stem_v3.mp4, ...; earlier videos are never overwritten
    name, n = f"{stem}.mp4", 1
    while name in existing:
        n += 1
        name = f"{stem}_v{n}.mp4"
    return name
