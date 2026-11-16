from convert.adapters.solidworks.Config.CutEquation import ConfigSketch, EquationDim
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
    ArchiveError,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.LocalFrame import ReadLocalPart
from convert.adapters.solidworks.Sketch.DimHandle import ReadDimRoute, ReadRefTail
from convert.adapters.solidworks.Sketch.InlineSketch import ParseInlineMut


# equation body readers must reach a fresh allocation and consume its typed fields
def OpenEqObject(Cursor: ArchiveCursor, ClassName: str) -> int:
    TagValue = ReadTag(Cursor.BlobValue, Cursor.Offset)
    RequireArch(
        TagValue.kind in (KDefinitionKind, KClassRefKind),
        True,
        "inline equation object",
    )
    _, _, ObjectIndex = Cursor.TakePointer(
        (ClassName,), TagValue.kind, CompactOnly=True
    )
    return ObjectIndex


# later dimension handles must resolve an observed sketch instead of materializing another identity
def ReadEqSketchMut(
    Cursor: ArchiveCursor, Sketches: dict[int, ConfigSketch]
) -> ConfigSketch:
    Start = Cursor.Offset
    TagValue = ReadTag(Cursor.BlobValue, Start)
    if TagValue.kind == KObjectRefKind:
        _, _, SketchIndex = Cursor.TakePointer(
            ("sgSketch",), KObjectRefKind, CompactOnly=True
        )
        Previous = Sketches.get(SketchIndex)
        if Previous is None:
            raise ArchiveError("equation refers to an unread sketch")
        return Previous
    RequireArch(len(Sketches) < 2, True, "two equation operand sketches")
    SketchIndex = OpenEqObject(Cursor, "sgSketch")
    Details = ParseInlineMut(Cursor, Start, SketchIndex, KConfigGen)
    Result = ConfigSketch(SketchIndex, Start, Cursor.Offset, Cursor.NextIndex, Details)
    Sketches[SketchIndex] = Result
    return Result


# display tokens corroborate the length slot selected by the typed native handle
def BindEqDim(
    Cursor: ArchiveCursor,
    Sketch: ConfigSketch,
    Start: int,
    SlotOffset: int,
    SlotIndex: int,
    LabelValue: str,
) -> EquationDim:
    Dimensions = Sketch.SketchData.Geometry["length_dimensions"]
    RequireArch(
        0 <= SlotIndex < len(Dimensions), True, "dimension slot in reached sketch"
    )
    Dimension = Dimensions[SlotIndex]
    ParamName = Dimension["name"]
    NamePrefix = f'"{ParamName}@'
    RequireArch(
        LabelValue.startswith(NamePrefix) and LabelValue.endswith('"'),
        True,
        "equation text identifies its saved dimension",
    )
    SketchName = LabelValue[len(NamePrefix) : -1]
    RequireArch(
        bool(SketchName) and '"' not in SketchName, True, "one saved sketch name"
    )
    return EquationDim(
        LabelValue,
        ParamName,
        SketchName,
        Sketch.SketchIndex,
        SlotIndex,
        Dimension["native_id"],
        Dimension["metres"],
        Start,
        Cursor.Offset,
        SlotOffset,
    )


# nested local components and dimension wrappers preserve the actual geometry owner
def ReadEqDim(Cursor: ArchiveCursor, Sketches: dict[int, ConfigSketch]) -> EquationDim:
    Start = Cursor.Offset
    _ = OpenEqObject(Cursor, "moRelDimension_c")
    RequireArch(Cursor.ReadInts("<H"), (0,), "empty dimension operand list")
    Cursor.ReadNull()
    _ = OpenEqObject(Cursor, "moDimRefWrapper_c")
    _ = Cursor.ReadPoint(1)
    _ = OpenEqObject(Cursor, "moSkDimHandleValG2_c")
    _, PartId = ReadLocalPart(Cursor, KConfigGen)
    RequireArch(PartId, 2, "equation dimension belongs to the local part")
    RequireArch(ReadDimRoute(Cursor), (0, -1, 0), "guarded equation dimension route")
    Sketch = ReadEqSketchMut(Cursor, Sketches)
    SlotOffset = Cursor.Offset
    (SlotIndex,) = Cursor.ReadInts("<i")
    ReadRefTail(Cursor)
    LabelValue = Cursor.ReadText()
    TypeCode, FirstPos, LastPos, Footer = Cursor.ReadInts("<4i")
    RequireArch((TypeCode, Footer), (1, 0), "saved dimension token framing")
    RequireArch(0 <= FirstPos < LastPos, True, "ordered dimension token positions")
    return BindEqDim(Cursor, Sketch, Start, SlotOffset, SlotIndex, LabelValue)
