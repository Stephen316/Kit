from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Planar.FaceBoundary import FaceBoundary
from convert.formats.Fusion.BrepCodec.Journal.Planar.VectorMath import (
    CrossProduct,
    DotProduct,
    Normalize,
    Subtract,
)


def CheckPlanarRing(
    FaceValue: FaceBoundary,
    Points: tuple[KJournalVector, ...],
    BodyPoints: tuple[KJournalVector, ...],
) -> None:
    Normal = Normalize(FaceValue.Surface.Normal)
    if FaceValue.Reversed:
        Normal = -Normal[0], -Normal[1], -Normal[2]
    if any(
        abs(DotProduct(Subtract(Point, FaceValue.Surface.OriginCm), Normal)) > 1e-7
        for Point in Points
    ):
        raise ValueError("Fusion face vertices leave their declared plane")
    for Index, Point in enumerate(Points):
        FirstEdge = Subtract(Points[(Index + 1) % len(Points)], Point)
        SecondEdge = Subtract(
            Points[(Index + 2) % len(Points)], Points[(Index + 1) % len(Points)]
        )
        if DotProduct(CrossProduct(FirstEdge, SecondEdge), Normal) <= 1e-12:
            raise ValueError("Fusion planar profile requires convex outward face rings")
    if any(
        DotProduct(Subtract(Point, Points[0]), Normal) > 1e-7 for Point in BodyPoints
    ):
        raise ValueError("Fusion planar profile requires a convex closed shell")
