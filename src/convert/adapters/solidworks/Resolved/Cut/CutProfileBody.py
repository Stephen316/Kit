from typing import TypedDict

from convert.adapters.solidworks.Container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.ContourChain import ProfileChain, ReadChain
from convert.adapters.solidworks.Resolved.Cut.CutEdgeRef import CutEdgeRef, ReadCutEdge


# the opaque kernel payload is reached and bounded before the archive map resumes
class KernelPacket(TypedDict):
    start: int
    end: int
    size: int


# saved profile framing keeps the chain namespace distinct from local sketch member ids
class CutProfileBody(TypedDict):
    sketch_object: int
    chain: ProfileChain
    kernel_packet: KernelPacket
    edge_references: list[CutEdgeRef]
    edge_order: tuple[int, ...]
    contour_flags: int
    support_offset: int
    next_map_index: int


# this profile lane uses one length framed kernel payload with no separate text selector
def ReadKernelMut(Cursor: ArchiveCursor) -> KernelPacket:
    RequireArch(
        Cursor.ReadInts("<iB"), (3, 0), "profile body and compact kernel selector"
    )
    (Length,) = Cursor.ReadInts("<i")
    Start = Cursor.Offset
    RequireArch(
        0 < Length <= len(Cursor.BlobValue) - Start, True, "bounded kernel packet"
    )
    Cursor.Offset += Length
    return {"start": Start, "end": Cursor.Offset, "size": Length}


# the full profile body reaches the effective face support after its projected edge array
def ReadCutBody(Cursor: ArchiveCursor, SketchIndex: int) -> CutProfileBody:
    RequireArch(Cursor.ReadInts("<Ii"), (1, 1), "one modern profile chain")
    Chain = ReadChain(Cursor)
    RequireArch(len(set(Chain["edge_ids"])), 4, "distinct cut region chain identities")
    Packet = ReadKernelMut(Cursor)
    RequireArch(Cursor.ReadInts("<i"), (0,), "empty profile pair map")
    RequireArch(Cursor.ReadInts("<H"), (4,), "four profile edge references")
    Edges = [ReadCutEdge(Cursor, KDefinitionKind)]
    Edges.extend(ReadCutEdge(Cursor, KClassRefKind) for _ in range(3))
    RequireArch(
        Cursor.ReadInts("<4I"), (4, 16, 1, 4), "observed profile edge index layout"
    )
    OrderValue = Cursor.ReadInts("<4I")
    RequireArch(set(OrderValue), set(range(1, 5)), "permutation of cut edge references")
    RequireArch(Cursor.ReadInts("<i"), (0,), "no secondary body packets")
    Flags, Count = Cursor.ReadInts("<IH")
    RequireArch(Count, 0, "empty contour object map")
    Cursor.ReadNull()
    return {
        "sketch_object": SketchIndex,
        "chain": Chain,
        "kernel_packet": Packet,
        "edge_references": Edges,
        "edge_order": OrderValue,
        "contour_flags": Flags,
        "support_offset": Cursor.Offset,
        "next_map_index": Cursor.NextIndex,
    }
