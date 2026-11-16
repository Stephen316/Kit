from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgFileHeader import DwgFileHeader
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgField,
    DwgRecord,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Records.CoerceValue import (
    AsBytes,
    AsInt,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Sections.RecordParts import RecordParts

# header start must remain consistent across callers so section boundaries and object references remain consistent
KHeaderStart = bytes.fromhex("cf7b1f23fdde38a95f7c68b84e6d335f")

# header finish must remain consistent across callers so section boundaries and object references remain consistent
KHeaderFinish = bytes.fromhex("3084e0dc0221c756a0839747b192cca0")

# header name must remain consistent across callers so section boundaries and object references remain consistent
KHeaderName = "AcDb:Header"

# header fill must remain consistent across callers so section boundaries and object references remain consistent
KHeaderFill = 0x55

# the frame names order must stay explicit so section boundaries and object references remain consistent
KFrameNames = ("TailWidth", "TailBits", "TrailBytes")


# the high word decision must stay consistent so section boundaries and object references remain consistent
def HasHighWord(FileHeader: DwgFileHeader) -> bool:
    return FileHeader.VersionText == "AC1032" or FileHeader.MaintenanceVersion > 3


# the reference width contract needs a shared interpretation so section boundaries and object references remain consistent
def RefWidth(Reference: DwgHandleRef) -> int:
    return 8 + 8 * ((Reference.RefValue.bit_length() + 7) // 8)


# the frame operation needs a consistent construction rule so section boundaries and object references remain consistent
def MakeFrame(TailWidth: int, TailBits: int, TrailBytes: bytes) -> DwgRecord:
    return DwgRecord(
        (
            DwgField("TailWidth", TailWidth),
            DwgField("TailBits", TailBits),
            DwgField("TrailBytes", TrailBytes),
        )
    )


# the frame parts contract needs a shared interpretation so section boundaries and object references remain consistent
def FrameParts(Frame: DwgRecord) -> tuple[int, int, bytes]:
    if not Frame.RecordFields:
        return 0, 0, b""
    TailWidth, TailBits, TrailBytes = RecordParts(Frame, KFrameNames)
    return AsInt(TailWidth), AsInt(TailBits), AsBytes(TrailBytes)
