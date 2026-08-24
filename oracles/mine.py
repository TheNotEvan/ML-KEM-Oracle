from __future__ import annotations

import os
import sys
from pathlib import Path

from .base import Oracle, Unsupported

_mlkem = None
_load_error: Exception | None = None

post_quantum_crypto = Path(
    os.environ.get("MLKEM_POST_QUANTUM_CRYPTO")
    or r"C:\Users\eperl\OneDrive\Documents\Post-Quantum-Crypto-main\Post-Quantum-Crypto-main"
)


def _load():

    global _mlkem, _load_error
    if _mlkem is not None or _load_error is not None:
        return _mlkem

    try:
        if not (post_quantum_crypto / "MLKEM" / "kem.py").is_file():
            raise ImportError("MLKEM/kem.py not found in Post-Quantum-Crypto, or set $MLKEM_POST_QUANTUM_CRYPTO")

        path = str(post_quantum_crypto)
        if not path in sys.path:
            sys.path.insert(0, path)

        from MLKEM import kem, params

        _mlkem = (kem, params)

    except (ImportError, OSError) as exc:
        _load_error = exc
    return _mlkem

class MineOracle(Oracle):

    name = "mine"

    def __init__(self, param_set: str = "ML-KEM-768"):
        super().__init__(param_set)
        module = _load()
        if module is None:
            raise Unsupported(f"Post-Quantum-Crypto not available: {_load_error}")
        self._kem, _params = module
        self._params = getattr(_params, param_set.replace("-", "_"))

    def _raw_keygen(self, d: bytes, z: bytes):
        return self._kem.key_gen_internal(d, z, self._params)

    def _raw_encapsulate(self, ek: bytes, m: bytes):
        return self._kem.encaps_internal(ek, m, self._params)

    def _raw_decapsulate(self, dk: bytes, ct: bytes):
        return self._kem.decaps_internal(dk, ct, self._params)
