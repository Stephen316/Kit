from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    KGrammarValue,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeBound import MakeBound
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken, KAsmValue

KLeafTags: dict[str, int] = {
    "real": 6,
    "int": 4,
    "enum": 21,
    "text": 7,
    "point": 19,
    "vector": 20,
}


def IsLeafValue(LeafKind: str, Value: KGrammarValue) -> bool:
    if LeafKind in ("int", "enum"):
        return type(Value) is int
    if LeafKind == "real":
        return type(Value) is float and IsFinite(Value)
    if LeafKind == "text":
        return type(Value) is str and Value.isascii()
    if LeafKind in ("point", "vector"):
        return (
            type(Value) is tuple
            and len(Value) == 3
            and all(type(Number) is float and IsFinite(Number) for Number in Value)
        )
    return False


def MakeLeaf(LeafKind: str, Value: KGrammarValue) -> tuple[KAsmToken, ...]:
    if LeafKind == "flag" and type(Value) is bool:
        return ((10 if Value else 11, None),)
    if LeafKind == "bound" and (Value is None or type(Value) is float):
        return MakeBound(Value)
    if LeafKind in KLeafTags and IsLeafValue(LeafKind, Value):
        return ((KLeafTags[LeafKind], CastValue(KAsmValue, Value)),)
    raise ValueError("Fusion grammar value disagrees with its leaf kind: " + LeafKind)
