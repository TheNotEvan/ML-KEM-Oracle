import csv
import random
import time
from pathlib import Path

import numpy as np

from oracles.mine import MineOracle, _load

_load()

from MLKEM import kpke
from MLKEM.params import n, q
from MLKEM.sampling import sample_poly_CBD as real_cbd
from MLKEM.ntt import ntt_inv
from MLKEM.encoding import byte_decode

PARAM_SET = "ML-KEM-768"
SCALES = (5, 6, 7)
KEYS = 60
ENCAPS = 150
SEED = 1234
RESULTS = Path(__file__).parent / "results" / "failure_correlation.csv"
FIELDS = ("param_set", "scale", "key", "s_norm_sq", "failures", "trials", "failure_rate", "seed")

_state = {"i": 0, "scale": 1}


def scaled_cbd(B, eta):
    i = _state["i"]
    _state["i"] += 1
    f = real_cbd(B, eta)
    if i < _state["k"]:
        return f
    return [(c * _state["scale"]) % q for c in f]


def s_norm_sq(dk, k):
    s = np.array([byte_decode(dk[i * 384:(i + 1) * 384], 12) for i in range(k)], dtype=np.int64)
    coef = np.array([ntt_inv(s[i]) for i in range(k)], dtype=np.int64)
    coef = np.where(coef > q // 2, coef - q, coef)
    return int((coef ** 2).sum())


def save_rows(rows):
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    new_file = not RESULTS.exists()
    with RESULTS.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerows(rows)


def run(scales=SCALES, keys=KEYS, encaps=ENCAPS, seed=SEED, param_set=PARAM_SET):
    rng = random.Random(seed)
    oracle = MineOracle(param_set)
    k = oracle.sizes.ek // 384
    _state["k"] = k
    rows = []

    kpke.sample_poly_CBD = scaled_cbd
    try:
        print(f"{'scale':>6} {'keys':>5} {'mean fail':>10} {'correlation':>12}")
        for scale in scales:
            _state["scale"] = scale
            norms, rates = [], []
            for key_i in range(keys):
                _state["i"] = 0
                ek, dk = oracle.keygen(rng.randbytes(32), rng.randbytes(32))

                fails = 0
                for _ in range(encaps):
                    _state["i"] = 0
                    ss, ct = oracle.encaps(ek, rng.randbytes(32))
                    _state["i"] = 0
                    if oracle.decaps(dk, ct) != ss:
                        fails += 1

                norm = s_norm_sq(dk, k)
                rate = fails / encaps
                norms.append(norm)
                rates.append(rate)
                rows.append({
                    "param_set": param_set, "scale": scale, "key": key_i,
                    "s_norm_sq": norm, "failures": fails, "trials": encaps,
                    "failure_rate": round(rate, 4), "seed": seed,
                })

            r = np.corrcoef(np.array(norms, float), np.array(rates, float))[0, 1]
            print(f"{scale:>6} {keys:>5} {np.mean(rates)*100:>9.1f}% {r:>12.3f}")
    finally:
        kpke.sample_poly_CBD = real_cbd

    save_rows(rows)
    print(f"\nwrote {len(rows)} rows -> {RESULTS}")


if __name__ == "__main__":
    t = time.time()
    run()
    print(f"{time.time()-t:.0f}s")