from convert.adapters.Fusion.Authoring.MakeRelations import MakeRelations
from convert.adapters.Fusion.Authoring.ProfileShape import (
    HasRectangle,
    ProfileCircle,
    ProfileLines,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryCurves import PointGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity


def MakeSketch(SpecValue: DocumentSpec) -> Sketch:
    Entities: list[SketchEntity] = []
    if HasRectangle(SpecValue):
        Lines = ProfileLines(SpecValue)
        Entities.extend(
            SketchEntity(
                f"point-{Index}",
                GeometryKind.KPoint,
                PointGeometry(LineValue.start),
                fixed=SpecValue.ConstrainRectangle and Index == 0,
            )
            for Index, LineValue in enumerate(Lines)
        )
        Entities.extend(
            SketchEntity(f"line-{Index}", GeometryKind.KLine, LineValue)
            for Index, LineValue in enumerate(Lines)
        )
        ProfileIds = tuple(f"line-{Index}" for Index in range(4))
    else:
        Entities.append(
            SketchEntity("circle", GeometryKind.KCircle, ProfileCircle(SpecValue))
        )
        ProfileIds = ("circle",)
    Relations = MakeRelations() if SpecValue.ConstrainRectangle else ()
    Params = (
        ("width-dimension", "depth-dimension") if SpecValue.ConstrainRectangle else ()
    )
    return Sketch(
        "sketch",
        SpecValue.SketchName,
        "plane",
        tuple(Entities),
        Relations,
        Params,
        (ProfileIds,),
    )
