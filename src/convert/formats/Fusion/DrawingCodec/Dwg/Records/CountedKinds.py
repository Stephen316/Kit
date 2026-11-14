from collections.abc import Callable

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import KDwgValue
from convert.formats.Fusion.DrawingCodec.Dwg.Records.CoerceValue import (
    AsBytes,
    AsRecord,
    AsText,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.GroupItems import (
    EncodeGroups,
    ReadGroupItems,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.WideText import (
    DecodeWide,
    EncodeWide,
)


def KeepBytes(DataValue: bytes) -> KDwgValue:
    return DataValue


KCountedReads: dict[str, Callable[[bytes], KDwgValue]] = {
    "Bytes": KeepBytes,
    "Groups": ReadGroupItems,
    "Wide": DecodeWide,
}


def EncodeCounted(KindText: str, Value: KDwgValue, ByteCount: int) -> bytes:
    if KindText == "Groups":
        DataValue = EncodeGroups(AsRecord(Value))
    elif KindText == "Wide":
        DataValue = EncodeWide(AsText(Value), ByteCount)
    else:
        DataValue = AsBytes(Value)
    if len(DataValue) != ByteCount:
        Label = "byte" if KindText == "Bytes" else KindText
        raise ValueError(f"DWG record {Label} field size mismatch")
    return DataValue
