from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundShape import (
    ApplyRounds,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.CapFaces import CapFaces
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import (
    KShapeFace,
    ShapeBody,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import KShapeEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFaces import WallFaces
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)


def CheckManifold(Faces: tuple[KShapeFace, ...]) -> None:
    UseSenses: dict[KShapeEdge, list[bool]] = {}
    for FaceValue in Faces:
        for LoopValue in FaceValue.Loops:
            for UseValue in LoopValue:
                UseSenses.setdefault(UseValue.Edge, []).append(UseValue.Forward)
    for Senses in UseSenses.values():
        if sorted(Senses) != [False, True]:
            raise ValueError("Fusion part shape is not a closed two-manifold")


def BuildShape(Solid: PrismSolid) -> ShapeBody:
    Faces: tuple[KShapeFace, ...] = (*WallFaces(Solid.Slabs), *CapFaces(Solid.Slabs))
    Shape = ShapeBody(
        Faces,
        Solid.BodyLabel,
        Solid.SketchCurves,
        0.0,
        Solid.EdgeTags,
        Ordinal=Solid.Ordinal,
    )
    if Solid.Rounds:
        Shape = ApplyRounds(Shape, Solid.Rounds)[0]
    CheckManifold(Shape.Faces)
    return Shape
