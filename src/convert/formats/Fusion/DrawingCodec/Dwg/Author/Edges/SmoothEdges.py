from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.EdgeVectors import (
    Length,
    Minus,
    UnitVector,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.PathPoints import PathPoint
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.SolidParts import (
    FlatFace,
    KEdgePath,
    KPointTriple,
    RoundFace,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewFrame import (
    Cross,
    DotProduct,
    Scaled,
)

KSmoothGap = 1e-6


def FaceNormal(Shape: FlatFace | RoundFace, Point: KPointTriple) -> KPointTriple:
    if isinstance(Shape, FlatFace):
        return Shape.Normal
    Offset = Minus(Point, Shape.Origin)
    Radial = UnitVector(
        Minus(Offset, Scaled(Shape.Along, DotProduct(Offset, Shape.Along)))
    )
    return UnitVector(Minus(Radial, Scaled(Shape.Along, Shape.Slope)))


def CheckSmooth(
    Built: tuple[FlatFace | RoundFace, ...],
    Paths: dict[str, KEdgePath],
    Owners: dict[str, list[int]],
) -> None:
    for EdgeKey, Curve in Paths.items():
        Sides = Owners.get(EdgeKey, [])
        if len(Sides) != 2 or Sides[0] == Sides[1]:
            raise ValueError(f"Authored DWG view edge {EdgeKey} must join two faces")
        Middle = PathPoint(Curve, 0.5)
        Former = FaceNormal(Built[Sides[0]], Middle)
        Latter = FaceNormal(Built[Sides[1]], Middle)
        if Length(Cross(Former, Latter)) < KSmoothGap:
            raise ValueError(
                f"Authored DWG view edge {EdgeKey} is tangent; no tangent edge rule"
            )
