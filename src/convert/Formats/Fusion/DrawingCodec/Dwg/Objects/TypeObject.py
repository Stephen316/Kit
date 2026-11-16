from dataclasses import replace as ReplaceFields

from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgObject import DwgObject
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord
from convert.Formats.Fusion.DrawingCodec.Dwg.Objects.EedCodec import ReadEedMut
from convert.Formats.Fusion.DrawingCodec.Dwg.Objects.EmitObject import EmitObject
from convert.Formats.Fusion.DrawingCodec.Dwg.Objects.LookupSpec import LookupSpec
from convert.Formats.Fusion.DrawingCodec.Dwg.Objects.RecordSpecs import KRecordSpecs
from convert.Formats.Fusion.DrawingCodec.Dwg.Records.ReadRecordMut import (
    ReadRecordMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Records.RecordStreams import (
    RecordStreams,
)


# the typed operation needs a distinct decoding boundary so section boundaries and object references remain consistent
def ParseTyped(
    Generic: DwgObject, CommonKind: str, ClassKind: str, VersionText: str
) -> DwgObject:
    Padding = -Generic.TailWidth & 7
    TailBytes = (Generic.TailValue << Padding).to_bytes(
        (Generic.TailWidth + Padding) // 8, "big"
    )
    Cursor = BitCursor(TailBytes, 0, Generic.TailWidth)
    Streams = RecordStreams(Cursor, Generic.TextItems, Generic.HandleRefs, VersionText)
    EedBlocks = ReadEedMut(Cursor)
    CommonData = ReadRecordMut(LookupSpec(CommonKind), Streams, ())
    ClassData = DwgRecord(())
    if ClassKind:
        ClassData = ReadRecordMut(LookupSpec(ClassKind), Streams, ())
    TailWidth = Cursor.Limit - Cursor.Position
    return ReplaceFields(
        Generic,
        EedBlocks=EedBlocks,
        CommonKind=CommonKind,
        CommonData=CommonData,
        ClassKind=ClassKind,
        ClassData=ClassData,
        TailWidth=TailWidth,
        TailValue=Cursor.TakeBits(TailWidth),
        TextItems=Generic.TextItems[Streams.TextIndex :],
        HandleRefs=Generic.HandleRefs[Streams.HandleIndex :],
    )


# the type object contract needs a shared interpretation so section boundaries and object references remain consistent
def TypeObject(
    Generic: DwgObject, ClassName: str, IsEntity: bool, VersionText: str
) -> DwgObject:
    CommonKind = "Entity" if IsEntity else "Object"
    Expected = EmitObject(Generic, VersionText)
    Choices = (ClassName, "") if ClassName in KRecordSpecs else ("",)
    for ClassKind in Choices:
        try:
            Typed = ParseTyped(Generic, CommonKind, ClassKind, VersionText)
        except ValueError:
            continue
        if EmitObject(Typed, VersionText) == Expected:
            return Typed
    return Generic
