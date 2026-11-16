from dataclasses import dataclass as Dataclass
from typing import NamedTuple

from convert.Geometry.Parasolid import (
    KLengthScale,
    KMissingParam,
    ParaWriteError,
    Vector,
    WriteFloatMut,
    WritePointerMut,
    WriteSignedMut,
    WriteTagMut,
)
from interchange.geometry.Models.VectorSpace import SpaceVector

# row framing is qualified for the pinned extended transmit layout
KPointSchema = "SCH_3701250_37102_13006"


# partition allocation assigns transport slots separately from kernel node identifiers
@Dataclass(frozen=True, slots=True)
class GhostAllocation:
    shell: int
    point: int
    vertex: int
    ghost_value: int
    point_node: int
    vertex_node: int


# the enclosing partition places these three records at their own graph positions
class GhostRows(NamedTuple):
    point: bytes
    vertex: bytes
    integer: bytes


# the surrounding typed stream determines the first occurrence of each class
class GhostRowMarks(NamedTuple):
    point: bool = True
    vertex: bool = True
    integer: bool = True


# the first class occurrence carries the optional marker before its node fields
def GhostRowHead(Kind: int, *, Marked: bool = True) -> bytearray:
    if type(Marked) is not bool:
        raise ParaWriteError("ghost row marker requires a boolean occurrence state")
    Result = bytearray()
    WriteTagMut(Result, Kind)
    if Marked:
        Result.append(0xFF)
    return Result


# the point stores its vertex plus empty attribute and sibling references
def EncodePointRow(
    PointMm: SpaceVector, Slots: GhostAllocation, *, Marked: bool = True
) -> bytes:
    Result = GhostRowHead(29, Marked=Marked)
    WritePointerMut(Result, Slots.point)
    WriteSignedMut(Result, Slots.point_node)
    for Reference in (0, Slots.vertex, 0, 0):
        WritePointerMut(Result, Reference)
    Vector(Result, PointMm, KLengthScale)
    return bytes(Result)


# the faceless vertex owns no fins or siblings and joins its shell and the point
def EncodeVertexRow(Slots: GhostAllocation, *, Marked: bool = True) -> bytes:
    Result = GhostRowHead(18, Marked=Marked)
    WritePointerMut(Result, Slots.vertex)
    WriteSignedMut(Result, Slots.vertex_node)
    for Reference in (0, 0, 0, 0, Slots.point):
        WritePointerMut(Result, Reference)
    WriteFloatMut(Result, KMissingParam)
    WritePointerMut(Result, Slots.shell)
    return bytes(Result)


# the witnessed ghost body identity occupies one signed integer in its value node
def EncodeIdRow(Slots: GhostAllocation, GhostId: int, *, Marked: bool = True) -> bytes:
    Result = GhostRowHead(82, Marked=Marked)
    WriteSignedMut(Result, 1)
    WritePointerMut(Result, Slots.ghost_value)
    WriteSignedMut(Result, GhostId)
    return bytes(Result)


# the caller's allocation and authored point determine the reciprocal owned records
def EncodeGhostRows(
    PointMm: SpaceVector,
    Slots: GhostAllocation,
    GhostId: int,
    *,
    Schema: str,
    Marks: GhostRowMarks = GhostRowMarks(),
) -> GhostRows:
    if Schema != KPointSchema:
        raise ParaWriteError("unsupported ghost point transmit schema")
    if not isinstance(Marks, GhostRowMarks):
        raise ParaWriteError("expected typed ghost row occurrence states")
    Indices = (Slots.shell, Slots.point, Slots.vertex, Slots.ghost_value)
    if len(set(Indices)) != 4 or not all(0 < Value < 32767 for Value in Indices):
        raise ParaWriteError("ghost point requires four distinct short transport slots")
    Nodes = (Slots.point_node, Slots.vertex_node)
    if len(set(Nodes)) != 2 or not all(0 < Value < 1 << 31 for Value in Nodes):
        raise ParaWriteError(
            "ghost point requires two distinct positive node identifiers"
        )
    if not 10000 < GhostId < 1 << 31:
        raise ParaWriteError("ghost body identifier is outside the allocated range")
    return GhostRows(
        EncodePointRow(PointMm, Slots, Marked=Marks.point),
        EncodeVertexRow(Slots, Marked=Marks.vertex),
        EncodeIdRow(Slots, GhostId, Marked=Marks.integer),
    )
