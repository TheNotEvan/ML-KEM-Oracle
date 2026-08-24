import random
import time
import csv
from pathlib import Path

from oracles.mine import MineOracle

BITS = (8,10,12,14,16)
TRIALS = 5
SEED = 1234

RESULTS = Path(__file__).parent / "results" / "recover_m.csv"
FIELDS = ("oracle", "param_set", "bits", "trial", "guesses", "seconds", "seed")

def save_rows(rows):
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    new_file = not RESULTS.exists()
    with RESULTS.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerows(rows)

def weak_m(value: int) -> bytes:
    return value.to_bytes(32, "big")


def recover_m(oracle, ek, ct, n_bits):
    for guess in range(1 << n_bits):
        m = weak_m(guess)
        ss, c = oracle.encaps(ek, m)
        if c == ct:
            return m, ss, guess + 1
    return None, None, 1 << n_bits

def run(bits=BITS, trials=TRIALS, seed=SEED, param_set="ML-KEM-768"):
    rng = random.Random(seed)
    oracle = MineOracle(param_set)
    ek, dk = oracle.random_keypair()

    print(f"{'bits':>5} {'trials':>7} {'mean':>10} {'expected':>10} {'sec/trial':>10}")
    for n in bits:
        counts = []
        rows = []
        t0 = time.time()
        for trial in range(trials):
            secret = rng.randrange(1 << n)
            ss_true, ct = oracle.encaps(ek, weak_m(secret))
            t1 = time.time()
            m_found, ss_found, guesses = recover_m(oracle, ek, ct, n)
            secs = time.time() - t1
            assert m_found == weak_m(secret) and ss_found == ss_true
            counts.append(guesses)
            rows.append({
                "oracle": oracle.name,
                "param_set": param_set,
                "bits": n,
                "trial": trial,
                "guesses": guesses,
                "seconds": round(secs, 4),
                "seed": seed,
            })
        per = (time.time() - t0) / trials
        mean = sum(counts) / len(counts)
        save_rows(rows)
        print(f"{n:>5} {trials:>7} {mean:>10.0f} {1 << (n - 1):>10} {per:>10.2f}")

if __name__ == "__main__":
    run()
