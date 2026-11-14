from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


def RefWord(Value: int) -> KAsmToken:
    return 12, Value


def IntWord(Value: int) -> KAsmToken:
    return 4, Value


def FloatWord(Value: float) -> KAsmToken:
    return 6, Value


def TextWord(Value: str) -> KAsmToken:
    return 7, Value


def LogicWord(Value: bool) -> KAsmToken:
    if type(Value) is not bool:
        raise ValueError("Fusion journal logical field requires a boolean")
    return (10 if Value else 11), None


def PointWord(Value: KJournalVector) -> KAsmToken:
    return 19, Value


def VectorWord(Value: KJournalVector) -> KAsmToken:
    return 20, Value


def NameWord(Value: str) -> KAsmToken:
    return 13, Value


def EnumWord(Value: int) -> KAsmToken:
    return 21, Value
