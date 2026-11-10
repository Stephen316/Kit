# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, AsmTable
from interchange.geometry.models.VectorSpace import SpaceVector


# field signatures qualify a typed record before any of its links are followed
def RequireAsm(
    Table: AsmTable, Identity: int, NameValue: str, Count: int | None = None
) -> AsmRecord:
    if not 0 <= Identity < len(Table.Records):
        raise ValueError("Fusion ASM pointer leaves initial topology")
    Value = Table.Records[Identity]
    if Value.Name != NameValue or (Count is not None and len(Value.Tokens) != Count):
        raise ValueError(f"Unsupported Fusion ASM {NameValue} record")
    return Value


# required scalar slots cannot be read as integers from alternate token tags
def ReadAsmInt(Value: AsmRecord, Index: int, TagValue: int = 4) -> int:
    if not 0 <= Index < len(Value.Tokens):
        raise ValueError("Truncated Fusion ASM record fields")
    Actual, Field = Value.Tokens[Index]
    if Actual != TagValue or type(Field) is not int:
        raise ValueError("Invalid Fusion ASM integer field")
    return Field


# linkage preserves the explicit null sentinel for optional entity pointers
def ReadAsmPtr(Value: AsmRecord, Index: int) -> int:
    Pointer = ReadAsmInt(Value, Index, 12)
    if Pointer < -1:
        raise ValueError("Invalid Fusion ASM entity pointer")
    return Pointer


# bounded text is part of the exact attribute schema rather than parsed loosely
def ReadAsmText(Value: AsmRecord, Index: int) -> str:
    if not 0 <= Index < len(Value.Tokens):
        raise ValueError("Truncated Fusion ASM text field")
    TagValue, TextValue = Value.Tokens[Index]
    if TagValue != 7 or not isinstance(TextValue, str):
        raise ValueError("Invalid Fusion ASM text field")
    return TextValue


# geometric checks read typed vectors only after topology identity is resolved
def ReadAsmVec(Value: AsmRecord, Index: int, TagValue: int) -> SpaceVector:
    Actual, Coords = Value.Tokens[Index]
    if Actual != TagValue or not isinstance(Coords, tuple) or len(Coords) != 3:
        raise ValueError("Invalid Fusion ASM geometric vector")
    return SpaceVector(*Coords)


# parameters retain numeric identity independently of endpoint geometry
def ReadAsmNum(Value: AsmRecord, Index: int) -> float:
    TagValue, Number = Value.Tokens[Index]
    if TagValue != 6 or type(Number) is not float:
        raise ValueError("Invalid Fusion ASM curve parameter")
    return Number


# orientation and flags use one of the two tagged boolean values
def IsAsmFlag(Value: AsmRecord, Index: int) -> bool:
    TagValue = Value.Tokens[Index][0]
    if TagValue not in (10, 11):
        raise ValueError("Invalid Fusion ASM topology flag")
    return TagValue == 10
