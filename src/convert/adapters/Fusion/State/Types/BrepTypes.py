from convert.Formats.Fusion.BrepCodec.Frustum.Models.ConeFrame import ConeFrame
from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.Formats.Fusion.BrepCodec.Frustum.Models.RimFrame import RimFrame
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.BrepCodec.Models.EntityIds import EntityIds
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.Formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.Formats.Fusion.BrepCodec.Models.SnapshotModel import SnapshotModel
from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.BrepCodec.Models.VertexIndices import VertexIndices
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismEdge import PrismEdge
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismLine import PrismLine
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismPlane import PrismPlane
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags

# the boundary representation types order must stay explicit so public document claims remain grounded in native records
KBrepTypes: tuple[type[object], ...] = (
    ConeFrame,
    FrustumFrame,
    FrustumHistory,
    RimFrame,
    AttribLinks,
    SketchAttrib,
    TagAttrib,
    TimeAttrib,
    TrackAttrib,
    AsmRoot,
    BodyNode,
    CoedgeNode,
    ConeNode,
    EdgeNode,
    EllipseNode,
    EntityPrefix,
    FaceNode,
    LoopNode,
    LumpNode,
    PlaneNode,
    PointNode,
    ShellNode,
    StraightNode,
    TransformNode,
    VertexNode,
    GeometryState,
    BodyIdentity,
    BrepHeader,
    EntityIds,
    FeatureTag,
    HistoryModel,
    HistoryState,
    SketchLink,
    SnapshotModel,
    TopologyTags,
    VertexIndices,
    PrismEdge,
    PrismFrame,
    PrismHistory,
    PrismLine,
    PrismPlane,
    PrismTags,
)
