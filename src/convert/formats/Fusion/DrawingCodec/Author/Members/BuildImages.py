from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DrawingCodec.Author.Defaults.DrawingPolicy import (
    KLargeThumb,
    KPreviewSide,
    KThumbSmall,
)
from convert.formats.Fusion.DrawingCodec.Author.Members.SheetPainter import (
    SheetImage,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetSizes import SheetSize
from convert.formats.Fusion.DrawingCodec.Model.DrawingNames import KImageFolders


def BuildImages(SheetId: str, SizeName: str) -> tuple[ContainerPart, ...]:
    Paper = SheetSize(SizeName)
    Aspect = Paper.PaperWidth / Paper.PaperHeight
    Previews, Thumbnails = KImageFolders
    Images = (
        (Thumbnails + SheetId + "_large.png", KLargeThumb),
        (Thumbnails + SheetId + "_small.png", KThumbSmall),
        (Previews + "small.png", (KPreviewSide, KPreviewSide)),
    )
    return tuple(
        ContainerPart(NameValue, SheetImage(Width, Height, Aspect))
        for NameValue, (Width, Height) in Images
    )
