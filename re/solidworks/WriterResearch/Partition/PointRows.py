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


# this schema uses the extended marker in front of the otherwise shared node fields
def GhostRowHead(Kind: int) -> bytearray:
    Result = bytearray()
    WriteTagMut(Result, Kind)
    Result.append(0xFF)
    return Result


# the point stores its vertex plus empty attribute and sibling references
def EncodePointRow(PointMm: SpaceVector, Slots: GhostAllocation) -> bytes:
    Result = GhostRowHead(29)
    WritePointerMut(Result, Slots.point)
    WriteSignedMut(Result, Slots.point_node)
    for Reference in (0, Slots.vertex, 0, 0):
        WritePointerMut(Result, Reference)
    Vector(Result, PointMm, KLengthScale)
    return bytes(Result)


# the faceless vertex owns no fins or siblings and joins its shell and the point
def EncodeVertexRow(Slots: GhostAllocation) -> bytes:
    Result = GhostRowHead(18)
    WritePointerMut(Result, Slots.vertex)
    WriteSignedMut(Result, Slots.vertex_node)
    for Reference in (0, 0, 0, 0, Slots.point):
        WritePointerMut(Result, Reference)
    WriteFloatMut(Result, KMissingParam)
    WritePointerMut(Result, Slots.shell)
    return bytes(Result)


# the witnessed ghost body identity occupies one signed integer in its value node
def EncodeIdRow(Slots: GhostAllocation, GhostId: int) -> bytes:
    Result = GhostRowHead(82)
    WriteSignedMut(Result, 1)
    WritePointerMut(Result, Slots.ghost_value)
    WriteSignedMut(Result, GhostId)
    return bytes(Result)


# the caller's allocation and authored point determine the reciprocal owned records
def EncodeGhostRows(
    PointMm: SpaceVector, Slots: GhostAllocation, GhostId: int, *, Schema: str
) -> GhostRows:
    if Schema != KPointSchema:
        raise ParaWriteError("unsupported ghost point transmit schema")
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
        EncodePointRow(PointMm, Slots),
        EncodeVertexRow(Slots),
        EncodeIdRow(Slots, GhostId),
    )
