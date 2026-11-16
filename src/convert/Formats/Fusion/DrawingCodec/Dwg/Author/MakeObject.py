from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgEed import DwgEed
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgObject import DwgObject
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord
from convert.Formats.Fusion.DrawingCodec.Dwg.Objects.LookupSpec import LookupSpec
from convert.Formats.Fusion.DrawingCodec.Dwg.Records.PutRecordMut import PutRecordMut
from convert.Formats.Fusion.DrawingCodec.Dwg.Records.RecordSinks import RecordSinks


# the object operation needs a consistent construction rule so drawing objects retain valid ownership and reference relationships
def MakeObject(
    TypeNumber: int,
    ObjectHandle: int,
    CommonData: DwgRecord,
    ClassKind: str,
    ClassData: DwgRecord,
    VersionText: str,
    EedBlocks: tuple[DwgEed, ...] = (),
) -> DwgObject:
    CommonKind = (
        "Entity" if CommonData.RecordFields[0].FieldName == "HasGraphics" else "Object"
    )
    Sinks = RecordSinks(VersionText)
    PutRecordMut(LookupSpec(CommonKind), CommonData, Sinks, ())
    PutRecordMut(LookupSpec(ClassKind), ClassData, Sinks, ())
    return DwgObject(
        TypeNumber,
        ObjectHandle,
        EedBlocks,
        CommonKind,
        CommonData,
        ClassKind,
        ClassData,
        0,
        0,
        (),
        bool(Sinks.TextItems),
        (),
    )
