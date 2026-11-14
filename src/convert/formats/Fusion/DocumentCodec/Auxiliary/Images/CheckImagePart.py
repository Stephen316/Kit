from re import fullmatch as FullMatch

from convert.formats.Fusion.ContainerCodec.ContainerLayout import KMaxPreviewSize
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart

KImageFolder = "Images.BlobParts/"
KImageName = r"Images\.BlobParts/Image\.[A-Fa-f0-9-]{36}\.png"
KImageMagic = b"\x89PNG\r\n\x1a\n"


def CheckImagePart(Value: ContainerPart) -> ContainerPart:
    if FullMatch(KImageName, Value.Name) is None:
        raise ValueError("Unsupported Fusion image part name")
    if (
        type(Value.Payload) is not bytes
        or not len(KImageMagic) < len(Value.Payload) <= KMaxPreviewSize
        or not Value.Payload.startswith(KImageMagic)
    ):
        raise ValueError("Fusion image part requires a PNG payload")
    return Value
