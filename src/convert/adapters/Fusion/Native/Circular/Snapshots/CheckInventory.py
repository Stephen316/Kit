from collections import Counter

from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)


def CheckInventory(State: GeometryState, HasSolid: bool) -> None:
    Bodies = 3 if HasSolid else 1
    Edges = 4 if HasSolid else 1
    Expected: dict[type[object], int] = {
        AsmRoot: 1,
        BodyNode: Bodies,
        LumpNode: Bodies,
        ShellNode: Bodies,
        FaceNode: 5 if HasSolid else 1,
        LoopNode: 6 if HasSolid else 1,
        CoedgeNode: 6 if HasSolid else 1,
        EdgeNode: Edges,
        VertexNode: Edges,
        PointNode: Edges,
        PlaneNode: 4 if HasSolid else 1,
        EllipseNode: Edges,
        SketchAttrib: 6 if HasSolid else 2,
    }
    if HasSolid:
        Expected.update({ConeNode: 1, TagAttrib: 5})
    if (
        Counter(type(Entity) for Entity in State.Entities) != Expected
        or State.Header.RootCount != Bodies + 1
    ):
        raise ValueError(
            "Native circular snapshot contains unaccounted geometry or attributes"
        )
