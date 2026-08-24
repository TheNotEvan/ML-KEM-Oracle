import csv
import random
import time
from pathlib import Path

from oracles.mine import MineOracle

DISTANCES = (0, 1, 2, 4, 16, 64, 256)
TRIALS = 500
SEED = 1234
RESULTS = Path(__file__).parent / "results" / "avalanche_d.csv"
FIELDS = ("oracle", "param_set", "flipped", "trial", "bits_differing", "total_bits", "percent", "seed")

def save_rows(rows):
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    new_file = not RESULTS.exists()
    with RESULTS.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerows(rows)

def flip_bits(seed: bytes, k: int, rng) -> bytes:
    position = rng.sample(range(len(seed) * 8), k)
    b = bytearray(seed)
    for p in position:
        b[p//8] ^= 1 << (p % 8)
    return bytes(b)

def bit_diff(a: bytes, b: bytes) -> int:
    return sum((x ^ y).bit_count() for x,y in zip(a,b))


def run(distances=DISTANCES, trials=TRIALS, seed=SEED, param_set="ML-KEM-768"):
    rng = random.Random(seed)
    oracle = MineOracle(param_set)
    z = bytes(32)
    rows = []

    print(f"{'flipped':>8} {'trials':>7} {'mean %':>9} {'min %':>8} {'max %':>8}")
    t0 = time.time()
    for k in distances:
        percents = []
        for trial in range(trials):
            d = bytes(rng.getrandbits(8) for _ in range(32))
            d2 = flip_bits(d, k, rng)

            ek, _ = oracle.keygen(d, z)
            ek2, _ = oracle.keygen(d2, z)

            differing = bit_diff(ek, ek2)
            total = len(ek) * 8
            percent = differing / total * 100
            percents.append(percent)

            rows.append({
                "oracle": oracle.name,
                "param_set": param_set,
                "flipped": k,
                "trial": trial,
                "bits_differing": differing,
                "total_bits": total,
                "percent": round(percent, 4),
                "seed": seed,
            })

        mean = sum(percents) / len(percents)
        print(f"{k:>8} {trials:>7} {mean:>8.2f}% {min(percents):>7.2f}% {max(percents):>7.2f}%")

    save_rows(rows)
    print(f"\n{time.time() - t0:.0f}s  |  wrote {len(rows)} rows -> {RESULTS}")


if __name__ == "__main__":
    run()
