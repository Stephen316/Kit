from __future__ import annotations

from typing import TYPE_CHECKING

from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.LocalFrame import ReadLocalPart
from convert.adapters.solidworks.Sketch.DimFields import ReadDistanceMut
from convert.adapters.solidworks.Sketch.DimHandle import ReadRefTail

if TYPE_CHECKING:
    from convert.adapters.solidworks.Sketch.Cursor import SketchArchive

# only these subclasses share the independently witnessed distance layout
KDistanceTypes = ("sgPntPntDist", "sgPntPntHorDist", "sgPntPntVertDist")

# these wrappers carry the local proxy through its typed feature and entity references
KProxyTypes = ("sgExtEnt_c", "moSketchExtRef_w", "moCompSketchEntHandle_c")

# common payload types are explicit so enclosing equation readers can delegate them
KSketchTypes = (
    KDistanceTypes
    + KProxyTypes
    + (
        "sgPointHandle",
        "sgLineHandle",
        "moPointBackedUpData_c",
        "moNodeName_c",
        "moLengthParameter_c",
    )
)


# proxy targets are usable only after the local part and entity handle resolve
def ReadLocalRefMut(Cursor: SketchArchive, ObjectIndex: int) -> None:
    _ = ReadLocalPart(Cursor, KConfigGen)
    FeatureId, TimeWord = Cursor.ReadInts("<iI")
    RequireArch(TimeWord < 0xFFFFFFFF, True, "compact feature reference time")
    Entity = Cursor.ReadObject("sgPointHandle", "sgLineHandle")
    Cursor.SketchReferences[ObjectIndex] = {
        "feature_id": FeatureId,
        "feature_time": TimeWord,
        "handle_class": Cursor.Objects[Entity],
        "handle_fields": Cursor.Handles[Entity],
    }
    _ = Cursor.ReadInts("<I")


# proxy wrappers preserve the target identity independently of their later display values
def ReadProxyMut(Cursor: SketchArchive, NameValue: str, ObjectIndex: int) -> None:
    if NameValue == "sgExtEnt_c":
        Wrapper = Cursor.ReadObject("moSketchExtRef_w")
        Cursor.SketchReferences[ObjectIndex] = Cursor.SketchReferences[Wrapper]
        for _ in range(3):
            _ = Cursor.ReadObject(None)
        _ = Cursor.ReadText()
    elif NameValue == "moSketchExtRef_w":
        Component = Cursor.ReadObject("moCompSketchEntHandle_c")
        Cursor.SketchReferences[ObjectIndex] = Cursor.SketchReferences[Component]
        ReadRefTail(Cursor)
        (Flags,) = Cursor.ReadInts("<h")
        RequireArch(-2 <= Flags <= 0, True, "valid external reference mode")
        _ = Cursor.ReadObject(None, "moPointBackedUpData_c")
    else:
        ReadLocalRefMut(Cursor, ObjectIndex)


# length values need their own saved node names before dimensions can bind them
def ReadLengthMut(Cursor: SketchArchive, ObjectIndex: int) -> None:
    NameIndex = Cursor.ReadObject("moNodeName_c")
    _ = Cursor.ReadInts("<4i")
    _ = Cursor.ReadText()
    _ = Cursor.ReadObject(None)
    Offset = Cursor.Offset
    (Value,) = Cursor.ReadPoint(1)
    RequireArch(Cursor.ReadInts("<B"), (0,), "absent native length override")
    NameValue = Cursor.NodeNames.get(NameIndex)
    if NameValue is None:
        raise ArchiveError("unbound local length parameter name")
    Cursor.Scalars[ObjectIndex] = NameValue, Value
    Cursor.ScalarOffsets[ObjectIndex] = Offset


# unsupported object classes must be rejected before their body can move the cursor
def ReadSketchMut(Cursor: SketchArchive, NameValue: str, ObjectIndex: int) -> None:
    if NameValue in ("sgPointHandle", "sgLineHandle"):
        (Index,) = Cursor.ReadInts("<H")
        RequireArch(Index < 0x777F, True, "short sketch handle index width")
        Owner, Flags = Cursor.ReadInts("<2i")
        Cursor.Handles[ObjectIndex] = Index, Owner, Flags
    elif NameValue in KProxyTypes:
        ReadProxyMut(Cursor, NameValue, ObjectIndex)
    elif NameValue == "moPointBackedUpData_c":
        _ = Cursor.ReadPoint(3)
    elif NameValue == "moNodeName_c":
        Cursor.NodeNames[ObjectIndex] = Cursor.ReadText()
    elif NameValue == "moLengthParameter_c":
        ReadLengthMut(Cursor, ObjectIndex)
    elif NameValue in KDistanceTypes:
        ReadDistanceMut(Cursor, NameValue)
    else:
        raise ArchiveError(
            f"Unsupported materialization of {NameValue} at {Cursor.Offset}"
        )
