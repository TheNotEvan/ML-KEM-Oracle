from __future__ import annotations

from .base import Oracle, Unsupported

_ml_kem = None
_load_error: Exception | None = None


def _load():

    global _ml_kem, _load_error
    if _ml_kem is not None or _load_error is not None:
        return _ml_kem

    try:
        from kyber_py import ml_kem

        _ml_kem = ml_kem

    except (ImportError, OSError) as exc:
        _load_error = exc
    return _ml_kem

class KyberPyOracle(Oracle):

    name = "kyber-py"

    def __init__(self, param_set: str = "ML-KEM-768"):
        super().__init__(param_set)
        module = _load()
        if module is None:
            raise Unsupported(f"kyber-py not available: {_load_error}")
        self._impl = getattr(module, param_set.replace("-", "_"))

    def _raw_keygen(self, d: bytes, z: bytes):
        return self._impl._keygen_internal(d, z)

    def _raw_encapsulate(self, ek: bytes, m: bytes):
        return self._impl._encaps_internal(ek, m)

    def _raw_decapsulate(self, dk: bytes, ct: bytes):
        return self._impl._decaps_internal(dk, ct)
