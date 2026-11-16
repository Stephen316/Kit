from dataclasses import dataclass as Dataclass
from typing import NamedTuple

from convert.Geometry.Parasolid import (
    ParaWriteError,
    WritePointerMut,
    WriteSignedMut,
    WriteTagMut,
)
from .PointRows import GhostRowHead, KPointSchema
from .WorldRow import WriteRefField


# body topology reserves independent slots and node identifiers for both owners
@Dataclass(frozen=True, slots=True)
class GhostTopology:
    body: int
    shell: int
    region: int
    vertex: int
    shell_node: int
    region_node: int


# the point and its shell are interleaved with the region in native order
class ClosureRows(NamedTuple):
    shell: bytes
    region: bytes


# shell markers and region descriptors belong to independent class histories
class GhostTopoMarks(NamedTuple):
    shell: bool = True
    region_definition: bool = True


# the isolated vertex sits in a single shell with no face or wire edges
def EncodeShellRow(Slots: GhostTopology, *, Marked: bool = True) -> bytes:
    Result = GhostRowHead(13, Marked=Marked)
    WritePointerMut(Result, Slots.shell)
    WriteSignedMut(Result, Slots.shell_node)
    for Reference in (0, Slots.body, 0, 0, 0, Slots.vertex, Slots.region, 0):
        WritePointerMut(Result, Reference)
    return bytes(Result)


# a faceless point region uses the native void classification with no frame
def EncodeRegionRow(Slots: GhostTopology, *, WithDefinition: bool = True) -> bytes:
    if type(WithDefinition) is not bool:
        raise ParaWriteError("ghost region requires a boolean definition state")
    Result = bytearray()
    WriteTagMut(Result, 19)
    if WithDefinition:
        Result.append(9)
        Result.extend(b"C" * 6)
        WriteRefField(Result, "I", "frame", 230)
        Result.extend(b"C")
        WriteRefField(Result, "A", "owner", 12)
        Result.extend(b"Z")
    WritePointerMut(Result, Slots.region)
    WriteSignedMut(Result, Slots.region_node)
    for Reference in (0, Slots.body, 0, 0, Slots.shell, 0):
        WritePointerMut(Result, Reference)
    Result.extend(b"V")
    WritePointerMut(Result, 0)
    return bytes(Result)


# both rows must preserve distinct transport slots and reciprocal ownership
def EncodeGhostTopo(
    Slots: GhostTopology, *, Schema: str, Marks: GhostTopoMarks = GhostTopoMarks()
) -> ClosureRows:
    if Schema != KPointSchema:
        raise ParaWriteError("unsupported ghost topology transmit schema")
    if not isinstance(Marks, GhostTopoMarks):
        raise ParaWriteError("expected typed ghost topology occurrence states")
    Indices = (Slots.body, Slots.shell, Slots.region, Slots.vertex)
    if len(set(Indices)) != 4 or not all(0 < Value < 32767 for Value in Indices):
        raise ParaWriteError("ghost topology requires four distinct short slots")
    Nodes = (Slots.shell_node, Slots.region_node)
    if len(set(Nodes)) != 2 or not all(0 < Value < 1 << 31 for Value in Nodes):
        raise ParaWriteError("ghost topology requires two distinct positive node ids")
    return ClosureRows(
        EncodeShellRow(Slots, Marked=Marks.shell),
        EncodeRegionRow(Slots, WithDefinition=Marks.region_definition),
    )
