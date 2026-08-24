import pytest

from kat.vectors import explain_mismatch, load_encap_decap, load_keygen
from oracles.mine import MineOracle
from oracles.saarinen import SaarinenOracle
from oracles.kyberpy import KyberPyOracle

from pathlib import Path

HERE = Path(__file__).parent
VECTORS = HERE / "vectors"

KEYGEN = load_keygen(VECTORS / "ML-KEM-keyGen-FIPS203" / "internalProjection.json")
ENCAPS, DECAPS = load_encap_decap(VECTORS / "ML-KEM-encapDecap-FIPS203" / "internalProjection.json")

ORACLES = [MineOracle, SaarinenOracle, KyberPyOracle]

@pytest.mark.parametrize("cls", ORACLES, ids=lambda c: c.name)
def test_keygen(cls):
    for case in KEYGEN:
        oracle = cls(case.param_set)
        ek, dk = oracle.keygen(case.d, case.z)
        assert ek == case.ek, explain_mismatch(case.param_set, "ek", ek, case.ek)
        assert dk == case.dk, explain_mismatch(case.param_set, "dk", dk, case.dk)


@pytest.mark.parametrize("cls", ORACLES, ids=lambda c: c.name)
def test_encaps(cls):
    for case in ENCAPS:
        oracle = cls(case.param_set)
        ss, ct = oracle.encaps(case.ek, case.m)
        assert ct == case.c, explain_mismatch(case.param_set, "c", ct, case.c)
        assert ss == case.k, explain_mismatch(case.param_set, "k", ss, case.k)


@pytest.mark.parametrize("cls", ORACLES, ids=lambda c: c.name)
def test_decaps(cls):
    for case in DECAPS:
        oracle = cls(case.param_set)
        ss = oracle.decaps(case.dk, case.c)
        assert ss == case.k, explain_mismatch(case.param_set, "k", ss, case.k)
