from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.CrcSixteen import CrcSixteen
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgObject import DwgObject
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.EmitObject import EmitObject
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.ModularCodes import (
    EncodeSigned,
    EncodeUnsigned,
)

# object marker must remain consistent across callers so section boundaries and object references remain consistent
KObjectMarker = 0x0DCA

# handle block limit needs one explicit bound so native drawing reconstruction cannot accept inconsistent resource or layout limits
KHandleBlockLimit = 2031


# the objects operation needs a consistent construction rule so section boundaries and object references remain consistent
def EmitObjects(
    DwgObjects: tuple[DwgObject, ...], VersionText: str
) -> tuple[bytes, dict[int, int]]:
    Output = bytearray(PackFields("<I", KObjectMarker))
    Offsets: dict[int, int] = {}
    for DwgItem in DwgObjects:
        if DwgItem.ObjectHandle in Offsets:
            raise ValueError(f"DWG handle {DwgItem.ObjectHandle:#x} is duplicated")
        Offsets[DwgItem.ObjectHandle] = len(Output)
        Output += EmitObject(DwgItem, VersionText)
    return bytes(Output), Offsets


# the frame block contract needs a shared interpretation so section boundaries and object references remain consistent
def FrameBlock(BlockValue: bytes) -> bytes:
    Opening = PackFields(">H", len(BlockValue) + 2) + BlockValue
    return Opening + PackFields(">H", CrcSixteen(0xC0C1, Opening))


# the handles operation needs a consistent construction rule so section boundaries and object references remain consistent
def EmitHandles(Offsets: dict[int, int]) -> bytes:
    Output = bytearray()
    BlockValue = bytearray()
    LastHandle = 0
    LastOffset = 0
    for Handle in sorted(Offsets):
        BlockValue += EncodeUnsigned(Handle - LastHandle)
        BlockValue += EncodeSigned(Offsets[Handle] - LastOffset)
        LastHandle, LastOffset = Handle, Offsets[Handle]
        if len(BlockValue) + 2 >= KHandleBlockLimit:
            Output += FrameBlock(bytes(BlockValue))
            BlockValue = bytearray()
            LastHandle, LastOffset = 0, 0
    if BlockValue:
        Output += FrameBlock(bytes(BlockValue))
    return bytes(Output) + FrameBlock(b"")
