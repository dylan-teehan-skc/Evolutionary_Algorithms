def improved_generations(history):
    # generation 0 plus every generation whose best score beat all earlier ones (VID-02)
    picked = []
    for h in history:
        if not picked or h["best_score"] > picked[-1]["best_score"]:
            picked.append(h)
    return picked
