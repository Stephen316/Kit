from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Round.SphereNode import SphereNode
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from convert.formats.Fusion.BrepCodec.Journal.Round.MakeSphereNode import MakeSphereNode
from convert.formats.Fusion.BrepCodec.Journal.Round.MakeTorusNode import MakeTorusNode
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakePointNode import (
    MakePointNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakePlaneNode import (
    MakePlaneNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeEllipseNode import (
    MakeEllipseNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeConeNode import (
    MakeConeNode,
)

from convert.formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode
from convert.formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeStraight import (
    MakeStraight,
)

from convert.formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeTransform import (
    MakeTransform,
)


def MakeCarriers(Value: KJournalEntity) -> AsmRecord:
    if isinstance(Value, SphereNode):
        return MakeSphereNode(Value)
    if isinstance(Value, TorusNode):
        return MakeTorusNode(Value)
    if isinstance(Value, TransformNode):
        return MakeTransform(Value)
    if isinstance(Value, StraightNode):
        return MakeStraight(Value)
    if isinstance(Value, PointNode):
        return MakePointNode(Value)
    if isinstance(Value, PlaneNode):
        return MakePlaneNode(Value)
    if isinstance(Value, EllipseNode):
        return MakeEllipseNode(Value)
    if isinstance(Value, ConeNode):
        return MakeConeNode(Value)
    raise ValueError("Unsupported Fusion journal entity variant")
