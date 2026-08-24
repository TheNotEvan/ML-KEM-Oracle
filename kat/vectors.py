from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

PARAM_SETS = ("ML-KEM-512", "ML-KEM-768", "ML-KEM-1024")

_K = {"ML-KEM-512": 2, "ML-KEM-768": 3, "ML-KEM-1024": 4}

def dk_sections(param_set: str) -> list[tuple[int,int,str]]:

    k = _K[param_set]
    dk_pke = 384 * k
    ek = 384 * k + 32
    return [
        (0, dk_pke, "dk_PKE (secret s-hat)"),
        (dk_pke, dk_pke + ek, "ek (embedded encapsulation key)"),
        (dk_pke + ek, dk_pke + ek + 32, "H(ek)"),
        (dk_pke + ek + 32, dk_pke + ek + 64, "z (implicit-rejection seed)"),
    ]

def explain_mismatch(param_set: str, field: str, got: bytes, want: bytes) -> str:
    if len(got) != len(want):
         return (f"{field}: wrong length — got {len(got)} bytes, "f"expected {len(want)} for {param_set}")
    if got == want:
        return f"{field} equal"

    off = next(i for i in range(len(got)) if got[i] != want[i])
    ndiff = sum(a != b for a,b in zip(got,want))

    where = ""
    if field == "dk":
        for start, end, name in dk_sections(param_set):
            if start <= off < end:
                where = f" — inside {name} (bytes {start}..{end})"
                break
 
    return (
        f"{field} mismatch on {param_set}: first differs at byte {off}{where}; "
        f"{ndiff}/{len(want)} bytes differ\n"
        f"    got  ...{got[off:off + 16].hex()}\n"
        f"    want ...{want[off:off + 16].hex()}"
    )

def _pick(name: tuple[str, ...], *objs: dict):
    for obj in objs:
        for n in name:
            if n in obj:
                return obj[n]

    seen = sorted({k for o in objs for k in o})
    raise KeyError(f"none of {name} present; keys available: {seen}")

def _hexfield(names: tuple[str, ...], *objs: dict) -> bytes:
    return bytes.fromhex(_pick(names, *objs))

@dataclass(frozen=True)
class KeyGenCase:
    param_set: str
    tc_id: int
    d: bytes
    z: bytes
    ek: bytes
    dk: bytes
 
 
@dataclass(frozen=True)
class EncapCase:
    param_set: str
    tc_id: int
    ek: bytes
    m: bytes
    c: bytes
    k: bytes
 
 
@dataclass(frozen=True)
class DecapCase:
    param_set: str
    tc_id: int
    dk: bytes
    c: bytes
    k: bytes
    reason: str | None

    @property
    def is_reject_case(self) -> bool:
        return self.reason is not None and self.reason != "no modification"


def load_keygen(path: str | Path) -> list[KeyGenCase]:
    doc = json.loads(Path(path).read_text())
    cases = []
    for g in doc["testGroups"]:
        ps = _pick(("parameterSet",), g)
        for t in g["tests"]:
            cases.append(KeyGenCase(
                param_set=ps,
                tc_id=t["tcId"],
                d=_hexfield(("d",), t, g),
                z=_hexfield(("z",), t, g),
                ek=_hexfield(("ek", "encapsulationKey"), t, g),
                dk=_hexfield(("dk", "decapsulationKey"), t, g),
            ))
    return cases

def load_encap_decap(path: str | Path) -> tuple[list[EncapCase], list[DecapCase]]:
    doc = json.loads(Path(path).read_text())
    encaps: list[EncapCase] = []
    decaps: list[DecapCase] = []
 
    for g in doc["testGroups"]:
        ps = _pick(("parameterSet",), g)
        fn = g.get("function")
        if fn is None:  
            fn = "encapsulation" if g.get("testType") == "AFT" else "decapsulation"
 
        for t in g["tests"]:
            if fn == "encapsulation":
                encaps.append(EncapCase(
                    param_set=ps,
                    tc_id=t["tcId"],
                    ek=_hexfield(("ek", "encapsulationKey"), t, g),
                    m=_hexfield(("m",), t, g),
                    c=_hexfield(("c", "ct", "ciphertext"), t, g),
                    k=_hexfield(("k", "ss", "sharedSecret"), t, g),
                ))
            else:
                decaps.append(DecapCase(
                    param_set=ps,
                    tc_id=t["tcId"],
                    dk=_hexfield(("dk", "decapsulationKey"), t, g),
                    c=_hexfield(("c", "ct", "ciphertext"), t, g),
                    k=_hexfield(("k", "ss", "sharedSecret"), t, g),
                    reason=t.get("reason") or g.get("reason"),
                ))
 
    return encaps, decaps