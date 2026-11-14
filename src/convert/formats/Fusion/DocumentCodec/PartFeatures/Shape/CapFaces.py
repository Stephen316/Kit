from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.MoveSlab import (
    ShiftLabel,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.CapFace import CapFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.CapRings import CapRings
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.GroupRings import (
    GroupRings,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelSplit import (
    PointTable,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSlab import PrismSlab


def CopyLabel(Label: FaceLabel, Loops: tuple[tuple[ShapeUse, ...], ...]) -> FaceLabel:
    Owners = {
        UseValue.Edge.Span.Label.OperationIds
        for LoopValue in Loops
        for UseValue in LoopValue
        if isinstance(UseValue.Edge, LevelEdge)
    }
    if len(Owners) != 1:
        return Label
    Owner = next(iter(Owners))
    Width = len(Label.OperationIds)
    if len(Owner) <= Width or Owner[:Width] != Label.OperationIds:
        return Label
    if min(Owner[Width:]) < 0:
        return Label
    return ShiftLabel(Label, Owner[Width:])


def CapFaces(Slabs: tuple[PrismSlab, ...]) -> tuple[CapFace, ...]:
    Levels = sorted(
        {
            Value
            for SlabValue in Slabs
            for Value in (SlabValue.LowerCm, SlabValue.UpperCm)
        }
    )
    Faces: list[CapFace] = []
    Table = PointTable(Slabs)
    for Level in Levels:
        Below = next(
            (SlabValue for SlabValue in Slabs if SlabValue.UpperCm == Level), None
        )
        Above = next(
            (SlabValue for SlabValue in Slabs if SlabValue.LowerCm == Level), None
        )
        for Upward, Source in ((False, Above), (True, Below)):
            if Source is None:
                continue
            Rings = CapRings(Level, Upward, Below, Above, Table)
            Label = Source.RoofLabel if Upward else Source.FloorLabel
            for Loops in GroupRings(Rings, Upward):
                Faces.append(CapFace(Level, Upward, CopyLabel(Label, Loops), Loops))
    return tuple(Faces)
