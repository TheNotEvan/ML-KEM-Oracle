from .base import Oracle, Outcome

import os
from oracles.mine import MineOracle
from oracles.saarinen import SaarinenOracle
from oracles.kyberpy import KyberPyOracle

def compare(oracles, op, *args):
    outcomes = [Oracle.probe(oracle, op, *args) for oracle in oracles]
    new_set = set(outcomes)
    agreed = len(new_set) == 1
    return agreed, outcomes

def sweep(oracles, trials=1000):
    found = []
    for _ in range(trials):
         d, z, m = os.urandom(32), os.urandom(32), os.urandom(32)
         agreed, outcomes = compare(oracles, "keygen", d,z)
         if not agreed:
             found.append(("keygen", (d,z), outcomes))
             continue
         ek, dk = outcomes[0].value

         agreed, outcomes = compare(oracles, "encaps", ek, m)
         if not agreed:
            found.append(("encaps", (ek, m), outcomes))
            continue
         
         ss, ct = outcomes[0].value

         agreed, outcomes = compare(oracles, "decaps", dk, ct)
         if not agreed:
            found.append(("decaps", (dk, ct), outcomes))
    return found