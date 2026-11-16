from struct import pack as PackFields
from typing import NamedTuple

from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import (
    KDefinitionKind,
    KMaxMapIndex,
    EncodeNull,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import (
    ArchiveCursor,
    FieldCursor,
)
from convert.adapters.solidworks.Container.Definition import ArchiveWriter
from convert.adapters.solidworks.Resolved.BossEnd import ReadStartHead

# the first boss end specification and its separate start wrapper each allocate an object
KBlindEndClass = "moEndSpec_c"
KFromEndClass = "moFromEndSpec_c"
KFromEndSchema = 1

# the native store includes both inline surface lists even when their counts are empty
KSurfaceLists = (1, 0, 1, 0)

# the ordinary first solid starts from its profile sketch plane
KSketchPlane = 0

# the ordinary solid extrusion constructor supplies these two separate return members
KExtrusionReturn = (0.0, -1)


# the parent words are retained separately because the native reader does not discard them
class EndProps(NamedTuple):
    cap_end_first: int
    cap_end_second: int
    delete_initial_face: int
    knit_result: int
    create_capped_solid: int


# the native post display route is the first ordinary blind extrusion in a part
def WriteEndStart(Writer: ArchiveWriter, *, Generation: int) -> int:
    RequireArch(Generation, KConfigGen, "plain modern blind boss end")
    NextIndex = Writer.next_index
    RequireArch(
        10 < NextIndex < KMaxMapIndex
        and Writer.classes.get(KBlindEndClass) == NextIndex - 10
        and Writer.classes.get("moFeatureDimHandle_c") == NextIndex - 7
        and Writer.classes.get("ParallelPlaneDistanceDim_c") == NextIndex - 5
        and KFromEndClass not in Writer.classes,
        True,
        "first blind display and end specification archive owners",
    )
    NullObject = EncodeNull()
    Writer.raw(
        NullObject  # absent second depth display
        + PackFields("<BHBHd6i", *KSurfaceLists, 0.0, *(0,) * 6)
        + NullObject * 2  # both draft angle displays absent
        + PackFields("<4i2H3i", *(0,) * 9)  # empty selections and separate solid scope
    )
    Writer.begin_object(KFromEndClass, KFromEndSchema)
    Writer.i32(KSketchPlane)
    return NextIndex + 1


# the typed reader shares the parent grammar and stops after the start wrapper's only field
def ReadEndStart(Cursor: ArchiveCursor, *, Generation: int) -> int:
    RequireArch(Generation, KConfigGen, "plain modern blind boss end")
    StartObject = ReadStartHead(Cursor, KDefinitionKind, 0)
    RequireArch(Cursor.ReadInts("<i"), (KSketchPlane,), "blind boss sketch-plane start")
    return StartObject


# preserve all signed source properties without asserting a constructive default
def ReadEndProps(Cursor: FieldCursor, *, Generation: int) -> EndProps:
    RequireArch(Generation, KConfigGen, "plain modern blind boss end properties")
    return EndProps(*Cursor.ReadInts("<5i"))


# a fresh ordinary extrusion starts with the native end constructor's clear fields
def EncodeFreshProps(*, Generation: int) -> bytes:
    RequireArch(Generation, KConfigGen, "fresh ordinary blind solid end properties")
    return PackFields("<5i", *EndProps(0, 0, 0, 0, 0))


# the extrusion returns only after the independently owned end specification closes
def EncodeBossReturn(*, Generation: int) -> bytes:
    RequireArch(Generation, KConfigGen, "plain modern blind boss outer return")
    return PackFields("<di", *KExtrusionReturn)
