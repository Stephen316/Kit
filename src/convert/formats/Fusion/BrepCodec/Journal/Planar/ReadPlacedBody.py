from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Planar.BuildPlanarBody import (
    BuildPlanarBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.formats.Fusion.BrepCodec.Journal.Planar.MapPlanarBody import MapPlanarBody
from convert.formats.Fusion.BrepCodec.Journal.Planar.PlanarShell import PlanarShell
from convert.formats.Fusion.BrepCodec.Journal.Planar.RequireLive import RequireLive


def ReadPlacedBody(Table: LiveTable, BodyRef: int) -> PlanarShell:
    Model = BuildPlanarBody(Table, BodyRef)
    BodyValue = RequireLive(Table, BodyRef, BodyNode)
    if BodyValue.TransformRef == -1:
        return Model
    Placement = RequireLive(Table, BodyValue.TransformRef, TransformNode)
    return MapPlanarBody(Model, Placement)
