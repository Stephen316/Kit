from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.geometry.Models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# the profile lines contract needs a shared interpretation so public document claims remain grounded in native records
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


# the profile circle contract needs a shared interpretation so public document claims remain grounded in native records
def ProfileCircle(SpecValue: DocumentSpec) -> CircleGeometry:
    return CircleGeometry(PlaneVector(0.0, 0.0), SpecValue.RadiusMm)


# the solid decision must stay consistent so public document claims remain grounded in native records
def HasSolid(SpecValue: DocumentSpec) -> bool:
    return SpecValue.ProfileKind in ("extrusion", "cuboid", "frustum")


# the rectangle decision must stay consistent so public document claims remain grounded in native records
def HasRectangle(SpecValue: DocumentSpec) -> bool:
    return SpecValue.ProfileKind in ("rectangle", "cuboid")
