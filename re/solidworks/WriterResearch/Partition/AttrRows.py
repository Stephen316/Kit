from dataclasses import dataclass as Dataclass

from convert.Geometry.Parasolid import ParaWriteError, WritePointerMut, WriteSignedMut
from .PointRows import GhostRowHead, KPointSchema

# the native point ghost registers this definition name in the geometry adapter
KGhostName = "GHOST_REF_BODY_ID_2001"


# attribute definition names and instances live in the partition transport graph
@Dataclass(frozen=True, slots=True)
class GhostAttributeSlots:
    name: int
    attribute: int
    definition: int
    body: int
    value: int
    node: int


# the attribute definition references a native identifier string of measured width
def EncodeGhostName(NameIndex: int) -> bytes:
    Text = KGhostName.encode("ascii")
    Result = GhostRowHead(79)
    WriteSignedMut(Result, len(Text))
    WritePointerMut(Result, NameIndex)
    Result.extend(Text)
    return bytes(Result)


# each ghost attribute binds its shared definition and separate value to one body
def EncodeGhostInstance(
    Slots: GhostAttributeSlots, *, Schema: str, Marked: bool = True
) -> bytes:
    if Schema != KPointSchema:
        raise ParaWriteError("unsupported ghost attribute transmit schema")
    Indices = (Slots.name, Slots.attribute, Slots.definition, Slots.body, Slots.value)
    if len(set(Indices)) != 5 or not all(0 < Value < 32767 for Value in Indices):
        raise ParaWriteError("ghost attribute requires five distinct short slots")
    if not 0 < Slots.node < 1 << 31:
        raise ParaWriteError("ghost attribute requires a positive node identifier")
    Result = GhostRowHead(81, Marked=Marked)
    WriteSignedMut(Result, 2)
    WritePointerMut(Result, Slots.attribute)
    WriteSignedMut(Result, Slots.node)
    for Reference in (Slots.definition, Slots.body, 0, 0, 0, 0, 0, Slots.value):
        WritePointerMut(Result, Reference)
    return bytes(Result)


# the single ghost profile files the shared definition name before its first instance
def EncodeGhostAttr(Slots: GhostAttributeSlots, *, Schema: str) -> bytes:
    Instance = EncodeGhostInstance(Slots, Schema=Schema)
    return EncodeGhostName(Slots.name) + Instance
