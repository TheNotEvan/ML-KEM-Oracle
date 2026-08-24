import csv
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RESULTS = Path(__file__).parent / "results"
FIGS = Path(__file__).parent / "figures"
PEAK_SCALE = 7

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150, "savefig.bbox": "tight",
    "axes.grid": True, "grid.alpha": 0.3, "font.size": 10,
    "axes.titlesize": 11, "axes.labelsize": 10,
})


def load(name):
    with (RESULTS / name).open() as f:
        return list(csv.DictReader(f))


def fig_failure_correlation():
    rows = [r for r in load("failure_correlation.csv") if int(r["scale"]) == PEAK_SCALE]
    x = np.array([int(r["s_norm_sq"]) for r in rows], float)
    y = np.array([float(r["failure_rate"]) * 100 for r in rows], float)
    r = np.corrcoef(x, y)[0, 1]

    fig, ax = plt.subplots(figsize=(6, 4.2))
    ax.scatter(x, y, s=28, alpha=0.75, edgecolor="white", linewidth=0.5, zorder=3)
    m, b = np.polyfit(x, y, 1)
    xs = np.linspace(x.min(), x.max(), 100)
    ax.plot(xs, m * xs + b, "--", color="crimson", linewidth=1.5,
            label=f"least squares fit\nPearson r = {r:.3f}  (n = {len(x)})", zorder=2)
    ax.set_xlabel(r"secret key magnitude  $\|s\|^2$")
    ax.set_ylabel("decryption failure rate (%)")
    ax.set_title(f"Failure rate vs secret magnitude ({PEAK_SCALE}x noise)")
    ax.legend(frameon=False, fontsize=9)
    fig.savefig(FIGS / "fig1_failure_correlation.png")
    plt.close(fig)
    return r


def fig_scale_response():
    rows = load("failure_correlation.csv")
    by = defaultdict(list)
    for r in rows:
        by[int(r["scale"])].append((int(r["s_norm_sq"]), float(r["failure_rate"])))
    scales = sorted(by)
    means = [np.mean([v for _, v in by[s]]) * 100 for s in scales]
    corrs = [np.corrcoef([a for a, _ in by[s]], [v for _, v in by[s]])[0, 1] for s in scales]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.8))
    a1.plot(scales, means, "o-", color="steelblue")
    a1.set_xlabel("noise amplification factor")
    a1.set_ylabel("mean failure rate (%)")
    a1.set_title("Failure rate")
    a1.set_xticks(scales)

    a2.plot(scales, corrs, "o-", color="crimson")
    a2.axhline(0, color="grey", linewidth=0.8)
    a2.set_xlabel("noise amplification factor")
    a2.set_ylabel(r"correlation of $\|s\|^2$ with failure rate")
    a2.set_title("Leak correlation")
    a2.set_xticks(scales)
    fig.suptitle("Response to noise amplification", fontsize=11)
    fig.savefig(FIGS / "fig2_scale_response.png")
    plt.close(fig)


def fig_recover_m():
    rows = load("recover_m.csv")
    by = defaultdict(list)
    for r in rows:
        by[int(r["bits"])].append(int(r["guesses"]))
    bits = sorted(by)
    means = [statistics.mean(by[b]) for b in bits]

    fig, ax = plt.subplots(figsize=(6, 4.2))
    for b in bits:
        ax.scatter([b] * len(by[b]), by[b], s=18, alpha=0.4, color="steelblue",
                   label="individual trials" if b == bits[0] else None, zorder=3)
    ax.plot(bits, means, "o-", color="steelblue", linewidth=1.6, label="measured mean", zorder=4)
    theory = [2 ** (b - 1) for b in bits]
    ax.plot(bits, theory, "--", color="crimson", linewidth=1.5, label=r"theory  $2^{n-1}$", zorder=2)
    ax.set_yscale("log", base=2)
    ax.set_xlabel("entropy in encapsulation coins m (bits)")
    ax.set_ylabel("guesses to recover shared secret")
    ax.set_title("Recovery cost vs entropy in m")
    ax.set_xticks(bits)
    ax.legend(frameon=False, fontsize=9)
    fig.savefig(FIGS / "fig3_recover_m.png")
    plt.close(fig)


def fig_avalanche():
    rows = load("avalanche_d.csv")
    by = defaultdict(list)
    for r in rows:
        by[int(r["flipped"])].append(float(r["percent"]))
    ks = sorted(by)
    means = [statistics.mean(by[k]) for k in ks]
    lo = [means[i] - min(by[k]) for i, k in enumerate(ks)]
    hi = [max(by[k]) - means[i] for i, k in enumerate(ks)]
    pos = np.arange(len(ks))

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.errorbar(pos, means, yerr=[lo, hi], fmt="o", capsize=4, color="steelblue",
                markersize=6, label="mean, with observed min/max")
    baseline = means[-1]
    ax.axhline(baseline, color="crimson", linestyle="--", linewidth=1.4,
               label=f"unrelated-key baseline ({baseline:.1f}%)")
    ax.set_xticks(pos)
    ax.set_xticklabels([str(k) for k in ks])
    ax.set_xlabel("bits flipped in seed d (out of 256)")
    ax.set_ylabel("% of public key bits differing")
    ax.set_ylim(-4, 60)
    ax.set_title("Key difference vs seed distance")
    ax.legend(frameon=False, fontsize=9, loc="center right")
    fig.savefig(FIGS / "fig4_avalanche.png")
    plt.close(fig)


if __name__ == "__main__":
    FIGS.mkdir(parents=True, exist_ok=True)
    r = fig_failure_correlation()
    fig_scale_response()
    fig_recover_m()
    fig_avalanche()
    for p in sorted(FIGS.glob("*.png")):
        print(f"{p.stat().st_size//1024:>5} KB  {p}")
