from convert.formats.Fusion.ContainerCodec.Preview.CheckPngBounds import CheckPngBounds
from struct import unpack_from as UnpackFrom
from zlib import crc32 as CrcValue


def CheckPreview(Payload: bytes) -> None:
    CheckPngBounds(Payload)
    Offset = 8
    HasData = False
    ChunkCount = 0
    while Offset + 12 <= len(Payload):
        Length = int(UnpackFrom(">I", Payload, Offset)[0])
        Finish = Offset + 12 + Length
        KindValue = Payload[Offset + 4 : Offset + 8]
        ChunkCount += 1
        if Finish > len(Payload) or ChunkCount > 4096 or not KindValue.isalpha():
            raise ValueError("Invalid Fusion PNG preview chunk")
        Checksum = int(UnpackFrom(">I", Payload, Finish - 4)[0])
        if CrcValue(Payload[Offset + 4 : Finish - 4]) != Checksum:
            raise ValueError("Fusion PNG preview checksum disagrees")
        if Offset != 8 and KindValue == b"IHDR":
            raise ValueError("Duplicate Fusion PNG preview header")
        if KindValue == b"IDAT":
            HasData = True
        if KindValue == b"IEND":
            if Length or Finish != len(Payload) or not HasData:
                raise ValueError("Invalid Fusion PNG preview termination")
            return
        Offset = Finish
    raise ValueError("Truncated Fusion PNG preview")
