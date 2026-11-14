from __future__ import annotations

from dataclasses import dataclass as MakeDataClass
from typing import Literal, TypeAlias

from convert.formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec

KWireKind: TypeAlias = Literal[
    "bool",
    "u8",
    "u16",
    "u32",
    "u64",
    "i32",
    "f32",
    "f64",
    "ascii",
    "utf16",
    "ref",
    "sequence",
    "set",
    "map",
    "pair",
    "optional",
    "fixed",
    "struct",
    "object",
    "matrix",
    "unsupported",
    "ge-array",
    "recipe",
    "sketch-tag",
]


@MakeDataClass(frozen=True, slots=True)
class WireType:
    KindValue: KWireKind
    Arguments: tuple[WireType, ...] = ()
    Members: tuple[FieldSpec[WireType], ...] = ()
    ClassGuid: str = ""
    FixedCount: int = 0
    AllowedInts: tuple[int, ...] = ()
    HasMatrixRows: bool = False
