from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

PARAM_SETS = ("ML-KEM-512", "ML-KEM-768", "ML-KEM-1024")

@dataclass (frozen=True)
class Sizes:
    ek: int
    dk: int
    ct: int
    ss: int = 32
    seed: int = 32

SIZES = {
    "ML-KEM-512": Sizes(ek=800, dk=1632, ct=768),
    "ML-KEM-768": Sizes(ek=1184, dk=2400, ct=1088),
    "ML-KEM-1024": Sizes(ek=1568, dk=3168, ct=1568),
}


@dataclass (frozen=True)
class Outcome:
    ok: bool
    value: object | None = None
    error: str | None = None
    detail: str | None = field(default=None, compare=False)

class OracleError(RuntimeError):
    pass

class Unsupported(OracleError):
    pass


def _as_bytes(value, *, what: str, expect: int | None = None) -> bytes:
    if isinstance(value, bytes):
        out = value
    elif isinstance(value, (bytearray, memoryview)) or isinstance(value, (list, tuple)) and all(isinstance(x, int) for x in value):
        out = bytes(value)
    else:
        raise OracleError(f"{what} must be bytes, bytearray, memoryview, or list/tuple of ints")
    if expect is not None and len(out) != expect:
        raise OracleError(f"{what}: expected {expect} bytes, got {len(out)}")

    return out

class Oracle(ABC):

    name: str = "unnamed"

    def __init__(self, param_set: str = "ML-KEM-768"):
        if param_set not in PARAM_SETS:
            raise OracleError(f"Unsupported parameter set: {param_set}")
        self.param_set = param_set
        self.sizes = SIZES[param_set]

    def __repr__(self) -> str:
        return f"<{self.name} {self.param_set}>"

    @abstractmethod
    def _raw_keygen(self, d: bytes, z: bytes): ...

    @abstractmethod
    def _raw_encapsulate(self, ek: bytes, m: bytes): ...

    @abstractmethod
    def _raw_decapsulate(self, dk: bytes, ct: bytes): ...


    def probe(self, op, *args):
        try:
            return Outcome(True, getattr(self, op)(*args))
        except Exception as exc:
            return Outcome(False, error=type(exc).__name__, detail=str(exc))


    def keygen(self, d:bytes, z: bytes) -> tuple[bytes, bytes]:
        d = _as_bytes(d, what="d", expect=self.sizes.seed)
        z = _as_bytes(z, what="z", expect=self.sizes.seed)
        ek, dk = self._unpack(self._raw_keygen(d,z) , what = f"{self.name}.keygen")
        return (_as_bytes(ek, what=f"{self.name}.keygen ek", expect=self.sizes.ek),
                _as_bytes(dk, what=f"{self.name}.keygen dk", expect=self.sizes.dk))

    def encaps(self, ek: bytes, m: bytes) -> tuple[bytes, bytes]:
        ek = _as_bytes(ek, what="ek", expect=self.sizes.ek)
        m = _as_bytes(m, what="m", expect=self.sizes.ss)
        ss, ct = self._unpack(self._raw_encapsulate(ek,m), what=f"{self.name}.encaps")
        return _as_bytes(ss, what=f"{self.name}.encaps ss", expect=self.sizes.ss),  _as_bytes(ct, what=f"{self.name}.encaps ct", expect=self.sizes.ct)
                

    def decaps(self, dk: bytes, ct: bytes) -> bytes:
        dk = _as_bytes(dk, what="dk", expect=self.sizes.dk)
        ct = _as_bytes(ct, what="ct", expect=self.sizes.ct)
        return _as_bytes(self._raw_decapsulate(dk, ct), what=f"{self.name}.decaps ss", expect=self.sizes.ss)

    def random_keypair(self) -> tuple[bytes, bytes]:
        return self.keygen(os.urandom(32), os.urandom(32))

    @staticmethod
    def _unpack(result, *, what: str):
        if not isinstance(result, (list, tuple)) or len(result) < 2:
            raise OracleError(f"{what}: expected a 2-tuple, got {type(result).__name__}")
        return result[0], result[1]

