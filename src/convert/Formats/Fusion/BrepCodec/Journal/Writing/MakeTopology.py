from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.WireNode import WireNode
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeWireNode import (
    MakeWireNode,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeAsmRoot import (
    MakeAsmRoot,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeBodyNode import (
    MakeBodyNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeLumpNode import (
    MakeLumpNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeShellNode import (
    MakeShellNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeFaceNode import (
    MakeFaceNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeLoopNode import (
    MakeLoopNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeCoedgeNode import (
    MakeCoedgeNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeEdgeNode import (
    MakeEdgeNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Geometry.MakeVertexNode import (
    MakeVertexNode,
)


# the topology operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakeTopology(Value: KJournalEntity) -> AsmRecord:
    if isinstance(Value, AsmRoot):
        return MakeAsmRoot(Value)
    if isinstance(Value, BodyNode):
        return MakeBodyNode(Value)
    if isinstance(Value, LumpNode):
        return MakeLumpNode(Value)
    if isinstance(Value, ShellNode):
        return MakeShellNode(Value)
    if isinstance(Value, WireNode):
        return MakeWireNode(Value)
    if isinstance(Value, FaceNode):
        return MakeFaceNode(Value)
    if isinstance(Value, LoopNode):
        return MakeLoopNode(Value)
    if isinstance(Value, CoedgeNode):
        return MakeCoedgeNode(Value)
    if isinstance(Value, EdgeNode):
        return MakeEdgeNode(Value)
    if isinstance(Value, VertexNode):
        return MakeVertexNode(Value)
    raise ValueError("Unsupported Fusion journal entity variant")
