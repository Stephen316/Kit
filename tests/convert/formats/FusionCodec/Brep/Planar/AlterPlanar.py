from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel


def AlterPlanar(Model: JournalModel, Fault: str) -> JournalModel:
    Entities = list(Model.Entities)
    for Index, Value in enumerate(Entities):
        if Fault == "face-winding" and isinstance(Value, FaceNode):
            Entities[Index] = ReplaceValue(Value, Reversed=not Value.Reversed)
            break
        if Fault == "curve-origin" and isinstance(Value, StraightNode):
            Entities[Index] = ReplaceValue(Value, OriginCm=(50.0, 60.0, 70.0))
            break
        if Fault == "zero-direction" and isinstance(Value, StraightNode):
            Entities[Index] = ReplaceValue(Value, DirectionVector=(0.0, 0.0, 0.0))
            break
        if Fault == "singular-transform" and isinstance(Value, TransformNode):
            Entities[Index] = ReplaceValue(Value, ScaleFactor=0.0)
            break
    else:
        raise ValueError("Unknown planar archive mutation")
    return ReplaceValue(Model, Entities=tuple(Entities))
