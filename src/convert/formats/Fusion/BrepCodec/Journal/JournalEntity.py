from typing import TypeAlias
from convert.formats.Fusion.BrepCodec.Journal.Complex.ComplexEntity import (
    KComplexEntity,
)
from convert.formats.Fusion.BrepCodec.Journal.Round.SphereNode import SphereNode
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode

from convert.formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.WireNode import WireNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.FeatureAttrib import (
    FeatureAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.NoMergeAttrib import (
    NoMergeAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.StitchAttrib import (
    StitchAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.VertedgeAttrib import (
    VertedgeAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.NestedTag import NestedTag
from convert.formats.Fusion.BrepCodec.Journal.Attributes.NameAttrib import NameAttrib

from convert.formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode

from convert.formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)

KJournalEntity: TypeAlias = (  # lgtm[py/unused-global-variable]
    AsmRoot
    | BodyNode
    | TransformNode
    | LumpNode
    | ShellNode
    | WireNode
    | FaceNode
    | LoopNode
    | CoedgeNode
    | EdgeNode
    | VertexNode
    | PointNode
    | PlaneNode
    | EllipseNode
    | StraightNode
    | ConeNode
    | SphereNode
    | TorusNode
    | TimeAttrib
    | FeatureAttrib
    | TrackAttrib
    | TagAttrib
    | SketchAttrib
    | StitchAttrib
    | NoMergeAttrib
    | VertedgeAttrib
    | NestedTag
    | NameAttrib
    | KComplexEntity
)
