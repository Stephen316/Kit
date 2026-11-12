from typing import TypeAlias

from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    ReadAsmInt,
    ReadAsmPtr,
    ReadAsmText,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, AsmTable

# recipe terms remain whole names with opaque counted numeric components
KNameTerms: TypeAlias = tuple[tuple[str, int, tuple[int, ...]], ...]


# both face and source coedge attributes reciprocate the original topology owner
def ReadAsmAttr(Table: AsmTable, Owner: int, HeadId: int) -> AsmRecord:
    Value = RequireAsm(Table, HeadId, "ATTRIB_CUSTOM-attrib")
    if (
        tuple(ReadAsmPtr(Value, Index) for Index in (0, 2, 3, 4)) != (-1, -1, -1, Owner)
        or ReadAsmInt(Value, 1) != -1
    ):
        raise ValueError("Fusion ASM named attribute owner disagrees")
    return Value


# all exact generic name fields are compared without assigning component semantics
def ReadFaceName(Table: AsmTable, Owner: int, FaceValue: AsmRecord) -> KNameTerms:
    Value = ReadAsmAttr(Table, Owner, ReadAsmPtr(FaceValue, 0))
    Count = ReadAsmInt(Value, 10)
    if (
        ReadAsmText(Value, 5) != "generic_tag_attrib_def"
        or ReadAsmText(Value, 9) != "generic_tag_attrib_def "
        or tuple(ReadAsmInt(Value, Index) for Index in (6, 7, 8)) != (3, 3, -1)
        or Count not in (1, 2, 3, 4, 5, 6, 8)
    ):
        raise ValueError("Unsupported Fusion ASM face name schema")
    Cursor = 11
    Terms: list[tuple[str, int, tuple[int, ...]]] = []
    for _ in range(Count):
        SizeValue = ReadAsmInt(Value, Cursor)
        NameValue = ReadAsmText(Value, Cursor + 1)
        Label = ReadAsmInt(Value, Cursor + 2)
        Length = ReadAsmInt(Value, Cursor + 3)
        if (
            not 1 <= SizeValue <= 128
            or len(NameValue) != SizeValue
            or not NameValue.isprintable()
            or not 0 <= Label <= 0xFFFFFFFF
            or not 0 <= Length <= 2
        ):
            raise ValueError("Invalid Fusion ASM counted face name")
        Components = tuple(
            ReadAsmInt(Value, Cursor + 4 + Index) for Index in range(Length)
        )
        if (
            any(not -0x80000000 <= PartValue <= 0x7FFFFFFF for PartValue in Components)
            or ReadAsmInt(Value, Cursor + 4 + Length) != 0
        ):
            raise ValueError("Invalid Fusion ASM face name component")
        Terms.append(
            (
                NameValue,
                Label,
                tuple(PartValue & 0xFFFFFFFF for PartValue in Components),
            )
        )
        Cursor += 5 + Length
    if Cursor != len(Value.Tokens):
        raise ValueError("Unexpected Fusion ASM face name trailer")
    return tuple(Terms)


# an exact sketch attribute names a curve tag on the original profile rim
def ReadCoedgeTag(Table: AsmTable, Owner: int, Coedge: AsmRecord) -> int | None:
    HeadId = ReadAsmPtr(Coedge, 0)
    if HeadId == -1:
        return None
    Value = ReadAsmAttr(Table, Owner, HeadId)
    TextValue = ReadAsmText(Value, 9).split(" ")
    if (
        len(Value.Tokens) != 10
        or ReadAsmText(Value, 5) != "sketch_attrib_def"
        or tuple(ReadAsmInt(Value, Index) for Index in (6, 7, 8)) != (1, 1, 3)
        or len(TextValue) != 6
        or TextValue[1:] != ["0", "0", "0", "1", "1"]
        or not TextValue[0].isdecimal()
        or not 1 <= len(TextValue[0]) <= 10
    ):
        raise ValueError("Unsupported Fusion ASM coedge sketch attribute")
    Identity = int(TextValue[0])
    if str(Identity) != TextValue[0] or Identity <= 0:
        raise ValueError("Invalid Fusion ASM coedge curve tag")
    return Identity
