from __future__ import annotations

import os
import sys
import types
from pathlib import Path

from .base import Oracle, Unsupported

_fips203 = None
_load_error: Exception | None = None

py_acvp_pqc = Path(
    os.environ.get("MLKEM_PY_ACVP_PQC")
    or r"C:\Users\eperl\OneDrive\Documents\py-acvp-pqc"
)


def _load():

    global _fips203, _load_error
    if _fips203 is not None or _load_error is not None:
        return _fips203

    try:
        if not (py_acvp_pqc / "fips203.py").is_file():
            raise ImportError("fips203.py not found in py-acvp-pqc. Clone mjosaarinen/py-acvp-pqc there, or set $MLKEM_PY_ACVP_PQC")

        path = str(py_acvp_pqc)
        if not path in sys.path:
            sys.path.insert(0, path)

        if "test_mlkem" not in sys.modules:
            stub = types.ModuleType("test_mlkem")
            stub.test_mlkem = lambda *args, **kwargs: None
            sys.modules["test_mlkem"] = stub

        import fips203

        _fips203 = fips203
        
    except (ImportError, OSError) as exc:
        _load_error = exc
    return _fips203

class SaarinenOracle(Oracle):

    name = "py-acvp-pqc"

    def __init__(self, param_set: str = "ML-KEM-768"):
        super().__init__(param_set)
        module = _load()
        if module is None:
            raise Unsupported(f"py-acvp-pqc not available: {_load_error}")
        self._impl = module.ML_KEM(param_set)

    def _raw_keygen(self, d: bytes, z: bytes):
        return self._impl.keygen_internal(d, z)

    def _raw_encapsulate(self, ek: bytes, m: bytes):
        return self._impl.encaps_internal(ek, m)

    def _raw_decapsulate(self, dk: bytes, ct: bytes):
        return self._impl.decaps_internal(dk, ct)