from re import fullmatch as FullMatch

from convert.formats.Fusion.ContainerCodec.ContainerLayout import KMaxPreviewSize
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart

# image folder must remain consistent across callers so supporting records retain their owning document relationships
KImageFolder = "Images.BlobParts/"

# image name must remain consistent across callers so supporting records retain their owning document relationships
KImageName = r"Images\.BlobParts/Image\.[A-Fa-f0-9-]{36}\.png"

# image magic must remain consistent across callers so supporting records retain their owning document relationships
KImageMagic = b"\x89PNG\r\n\x1a\n"


# invalid image part input must fail here so supporting records retain their owning document relationships
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
