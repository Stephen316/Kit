from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)


# the reference word contract needs a shared interpretation so revision ownership survives native history reconstruction
def RefWord(Value: int) -> KAsmToken:
    return 12, Value


# the int word contract needs a shared interpretation so revision ownership survives native history reconstruction
def IntWord(Value: int) -> KAsmToken:
    return 4, Value


# the float word contract needs a shared interpretation so revision ownership survives native history reconstruction
def FloatWord(Value: float) -> KAsmToken:
    return 6, Value


# the text word contract needs a shared interpretation so revision ownership survives native history reconstruction
def TextWord(Value: str) -> KAsmToken:
    return 7, Value


# logic word needs an explicit validity boundary so revision ownership survives native history reconstruction
def LogicWord(Value: bool) -> KAsmToken:
    if type(Value) is not bool:
        raise ValueError("Fusion journal logical field requires a boolean")
    return (10 if Value else 11), None


# the word operation needs one geometric convention so revision ownership survives native history reconstruction
def PointWord(Value: KJournalVector) -> KAsmToken:
    return 19, Value


# the word operation needs one geometric convention so revision ownership survives native history reconstruction
def VectorWord(Value: KJournalVector) -> KAsmToken:
    return 20, Value


# the name word contract needs a shared interpretation so revision ownership survives native history reconstruction
def NameWord(Value: str) -> KAsmToken:
    return 13, Value


# the enum word contract needs a shared interpretation so revision ownership survives native history reconstruction
def EnumWord(Value: int) -> KAsmToken:
    return 21, Value
