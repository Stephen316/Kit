from dataclasses import dataclass as Dataclass

from convert.Geometry.Parasolid import (
    ParaWriteError,
    WritePointerMut,
    WriteShortMut,
    WriteSignedMut,
    WriteTagMut,
)
from .PointRows import KPointSchema


# the enclosing allocation determines the world links and two independent counters
@Dataclass(frozen=True, slots=True)
class GhostWorld:
    world: int
    body: int
    definition: int
    highest_id: int
    current_id: int


# named descriptor fields identify what the versioned world schema inserts or appends
def WorldField(Record: str, Name: str) -> bytes:
    Encoded = Name.encode("ascii")
    return Record.encode("ascii") + bytes((len(Encoded),)) + Encoded


# reference descriptors name their kernel class and have one value
def WriteRefField(Result: bytearray, Record: str, Name: str, Kind: int) -> None:
    Result.extend(WorldField(Record, Name))
    WriteShortMut(Result, Kind)
    WriteShortMut(Result, 1)


# this class declaration describes all fields used by the following world row
def GhostWorldSchema() -> bytearray:
    Result = bytearray()
    WriteTagMut(Result, 101)
    Result.append(19)
    Result.extend(b"C" * 7)
    WriteRefField(Result, "I", "mesh", 1006)
    WriteRefField(Result, "I", "polyline", 1008)
    WriteRefField(Result, "I", "lattice", 222)
    Result.extend(b"CC")
    WriteRefField(Result, "I", "attdef_list", 74)
    Result.extend(b"CC")
    Result.extend(WorldField("A", "index_map_offset"))
    WriteSignedMut(Result, 1)
    Result.extend((1, ord("d")))
    WriteRefField(Result, "A", "index_map", 82)
    WriteRefField(Result, "A", "schema_embedding_map", 82)
    WriteRefField(Result, "A", "mesh_offset_data", 206)
    Result.append(ord("Z"))
    return Result


# the measured class and row end at the following body definition
def EncodeGhostWorld(State: GhostWorld, *, Schema: str) -> bytes:
    if Schema != KPointSchema:
        raise ParaWriteError("unsupported ghost world transmit schema")
    Indices = (State.world, State.body, State.definition)
    if len(set(Indices)) != 3 or not all(0 < Value < 32767 for Value in Indices):
        raise ParaWriteError("ghost world requires three distinct short slots")
    Result = GhostWorldSchema()
    WritePointerMut(Result, State.world)
    for Reference in (0, 0, State.body, 0, 0, 0, 0, 0, 0, 0):
        WritePointerMut(Result, Reference)
    Result.append(1)  # live world
    WritePointerMut(Result, State.definition)
    WritePointerMut(Result, 0)  # absent extended attribute definition list
    WriteSignedMut(Result, State.highest_id)
    WriteSignedMut(Result, State.current_id)
    WriteSignedMut(Result, 0)  # absent index map offset
    for _ in range(3):  # no index map, schema embedding map or mesh offset data
        WritePointerMut(Result, 0)
    return bytes(Result)
