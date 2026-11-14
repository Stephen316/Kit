from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFileHeader import DwgFileHeader
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgField,
    DwgRecord,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.CoerceValue import (
    AsBytes,
    AsInt,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.RecordParts import RecordParts

KHeaderStart = bytes.fromhex("cf7b1f23fdde38a95f7c68b84e6d335f")
KHeaderFinish = bytes.fromhex("3084e0dc0221c756a0839747b192cca0")
KHeaderName = "AcDb:Header"
KHeaderFill = 0x55
KFrameNames = ("TailWidth", "TailBits", "TrailBytes")


def HasHighWord(FileHeader: DwgFileHeader) -> bool:
    return FileHeader.VersionText == "AC1032" or FileHeader.MaintenanceVersion > 3


def RefWidth(Reference: DwgHandleRef) -> int:
    return 8 + 8 * ((Reference.RefValue.bit_length() + 7) // 8)


def MakeFrame(TailWidth: int, TailBits: int, TrailBytes: bytes) -> DwgRecord:
    return DwgRecord(
        (
            DwgField("TailWidth", TailWidth),
            DwgField("TailBits", TailBits),
            DwgField("TrailBytes", TrailBytes),
        )
    )


def FrameParts(Frame: DwgRecord) -> tuple[int, int, bytes]:
    if not Frame.RecordFields:
        return 0, 0, b""
    TailWidth, TailBits, TrailBytes = RecordParts(Frame, KFrameNames)
    return AsInt(TailWidth), AsInt(TailBits), AsBytes(TrailBytes)
