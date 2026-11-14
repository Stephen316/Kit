from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.geometry.models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.models.VectorPlane import PlaneVector


def ProfileLines(SpecValue: DocumentSpec) -> tuple[LineGeometry, ...]:
    Points = (
        PlaneVector(0.0, 0.0),
        PlaneVector(SpecValue.WidthMm, 0.0),
        PlaneVector(SpecValue.WidthMm, SpecValue.DepthMm),
        PlaneVector(0.0, SpecValue.DepthMm),
    )
    return tuple(
        LineGeometry(Points[Index], Points[(Index + 1) % 4]) for Index in range(4)
    )


def ProfileCircle(SpecValue: DocumentSpec) -> CircleGeometry:
    return CircleGeometry(PlaneVector(0.0, 0.0), SpecValue.RadiusMm)


def HasSolid(SpecValue: DocumentSpec) -> bool:
    return SpecValue.ProfileKind in ("extrusion", "cuboid", "frustum")


def HasRectangle(SpecValue: DocumentSpec) -> bool:
    return SpecValue.ProfileKind in ("rectangle", "cuboid")
