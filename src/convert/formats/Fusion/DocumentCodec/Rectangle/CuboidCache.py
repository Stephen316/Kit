from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakePoint


def CuboidCache(Author: AuthorState) -> list[dict[str, object]]:
    Width = Author.SpecValue.WidthMm / 10.0
    Depth = Author.SpecValue.DepthMm / 10.0
    Height = Author.SpecValue.LengthMm / 10.0
    Volume = Width * Depth * Height
    Fields: dict[str, object] = dict(
        area=2.0 * (Width * Depth + Width * Height + Depth * Height),
        areaPrec=0.0,
        cog=MakePoint(Width / 2.0, Depth / 2.0, Height / 2.0),
        inertiaPrec=0.0,
        moi=MakePoint(
            Volume * (Depth * Depth + Height * Height) / 3.0,
            Volume * (Width * Width + Height * Height) / 3.0,
            Volume * (Width * Width + Depth * Depth) / 3.0,
        ),
        moiOffDiag=MakePoint(
            -Volume * Width * Depth / 4.0,
            -Volume * Width * Height / 4.0,
            -Volume * Depth * Height / 4.0,
        ),
        revisionGuid=Author.RevisionId,
        volume=Volume,
        volumePrec=0.0,
    )
    return [Author.MakeGroup("MassPropertyCacheValue", Fields)]
