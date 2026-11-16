from typing import TypeAlias
from convert.Formats.Fusion.BrepCodec.Journal.Complex.ComplexEntity import (
    KComplexEntity,
)
from convert.Formats.Fusion.BrepCodec.Journal.Round.SphereNode import SphereNode
from convert.Formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.WireNode import WireNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.FeatureAttrib import (
    FeatureAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.NoMergeAttrib import (
    NoMergeAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.StitchAttrib import (
    StitchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.VertedgeAttrib import (
    VertedgeAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.NestedTag import NestedTag
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.NameAttrib import NameAttrib

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)

# the journal entity variants need one shared contract so journal reconstruction cannot omit a supported value shape
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
