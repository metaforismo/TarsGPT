"""The honesty check: does the simulator rank gaits like reality does?

Replays the parameters from your logged real-robot sessions through the sim
reward and reports the Spearman rank correlation. High correlation = the sim
is a useful pre-filter on your build; low = don't trust it, train for real.
"""


def _ranks(values: list[float]) -> list[float]:
    """Average-rank transform (ties share their mean rank)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        mean_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = mean_rank
        i = j + 1
    return ranks


def spearman(xs: list[float], ys: list[float]) -> float:
    """Spearman rank correlation, pure Python."""
    if len(xs) != len(ys) or len(xs) < 3:
        raise ValueError("need at least 3 paired samples")
    rx, ry = _ranks(xs), _ranks(ys)
    mx = sum(rx) / len(rx)
    my = sum(ry) / len(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sx = sum((a - mx) ** 2 for a in rx) ** 0.5
    sy = sum((b - my) ** 2 for b in ry) ** 0.5
    if sx == 0 or sy == 0:
        return 0.0
    return cov / (sx * sy)


def correlate_log(reward_fn, log_data: dict) -> tuple[float, int]:
    """Spearman correlation between logged real rewards and reward_fn
    re-evaluated on the same parameters. Returns (rho, samples_used)."""
    pairs = [(e["params"], e["reward"]) for e in log_data.get("entries", [])
             if e.get("params")]
    if len(pairs) < 3:
        raise ValueError(
            "need at least 3 logged evaluations with parameters - run a "
            "training session first (sessions before v1.6 did not log params)")
    sim_scores = [reward_fn(params) for params, _ in pairs]
    real_scores = [reward for _, reward in pairs]
    return spearman(sim_scores, real_scores), len(pairs)


def verdict(rho: float) -> str:
    if rho >= 0.6:
        return "strong - the sim is a useful pre-filter for this build"
    if rho >= 0.3:
        return "weak - use the sim only for coarse screening"
    return "none - do not trust the sim on this build, train for real"
