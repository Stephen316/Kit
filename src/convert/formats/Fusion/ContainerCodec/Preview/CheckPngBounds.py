from struct import unpack_from as UnpackFrom

from convert.formats.Fusion.ContainerCodec.ContainerLayout import (
    KMaxPreviewSize,
    KMaxPreviewSide,
)


def CheckPngBounds(Payload: bytes) -> None:
    if (
        type(Payload) is not bytes
        or not 57 <= len(Payload) <= KMaxPreviewSize
        or not Payload.startswith(b"\x89PNG\r\n\x1a\n")
    ):
        raise ValueError("Invalid Fusion PNG preview")
    if Payload[12:16] != b"IHDR" or UnpackFrom(">I", Payload, 8)[0] != 13:
        raise ValueError("Missing Fusion PNG preview header")
    Width, Height = UnpackFrom(">2I", Payload, 16)
    if not 0 < Width <= KMaxPreviewSide or not 0 < Height <= KMaxPreviewSide:
        raise ValueError("Oversized Fusion PNG preview dimensions")
