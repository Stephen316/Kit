from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitWriter import BitWriter
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutCodeMut import (
    PutHandleMut,
    PutObjTypeMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutTextsMut import PutTextsMut
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.CrcSixteen import CrcSixteen
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgObject import DwgObject
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.EedCodec import PutEedMut
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.LookupSpec import LookupSpec
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.ModularCodes import (
    EncodeModular,
    EncodeUnsigned,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.PutRecordMut import PutRecordMut
from convert.formats.Fusion.DrawingCodec.Dwg.Records.RecordSinks import RecordSinks


def FrameObjectMut(Writer: BitWriter, HandleRefs: tuple[DwgHandleRef, ...]) -> bytes:
    DataBits = Writer.BitCount
    for Reference in HandleRefs:
        PutHandleMut(Writer, Reference)
    Padding = -Writer.BitCount & 7
    Writer.PutBits((1 << Padding) - 1, Padding)
    BodyValue = Writer.ToBytes()
    Opening = EncodeModular(len(BodyValue)) + EncodeUnsigned(Writer.BitCount - DataBits)
    CrcValue = CrcSixteen(0xC0C1, Opening + BodyValue)
    return Opening + BodyValue + PackFields("<H", CrcValue)


def EmitObject(DwgItem: DwgObject, VersionText: str) -> bytes:
    Sinks = RecordSinks(VersionText)
    Writer = Sinks.DataWriter
    PutObjTypeMut(Writer, DwgItem.TypeNumber)
    PutHandleMut(Writer, DwgHandleRef(0, DwgItem.ObjectHandle))
    if DwgItem.CommonKind:
        PutEedMut(Writer, DwgItem.EedBlocks)
        PutRecordMut(LookupSpec(DwgItem.CommonKind), DwgItem.CommonData, Sinks, ())
    elif DwgItem.EedBlocks or DwgItem.ClassKind:
        raise ValueError("DWG object holds typed data without its common data")
    if DwgItem.ClassKind:
        PutRecordMut(LookupSpec(DwgItem.ClassKind), DwgItem.ClassData, Sinks, ())
    Writer.PutBits(DwgItem.TailValue, DwgItem.TailWidth)
    TextItems = (*Sinks.TextItems, *DwgItem.TextItems)
    PutTextsMut(Writer, TextItems, DwgItem.HasTexts)
    return FrameObjectMut(Writer, (*Sinks.HandleRefs, *DwgItem.HandleRefs))
