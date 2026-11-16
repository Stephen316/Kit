from convert.Formats.Fusion.BrepCodec.Journal.Complex.ComplexEntity import (
    KComplexTypes,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Writing.MakeComplex import (
    MakeComplex,
)
from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.BrepCodec.Journal.Round.SphereNode import SphereNode
from convert.Formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeTopology import MakeTopology
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeCarriers import MakeCarriers
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeAttributes import (
    MakeAttributes,
)
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
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.NestedTag import NestedTag
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.NameAttrib import NameAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.VertedgeAttrib import (
    VertedgeAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeSysAttrib import (
    MakeNoMerge,
    MakeStitchNode,
    MakeVertedge,
)

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode


from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)


# the entity node operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakeEntityNode(Value: KJournalEntity) -> AsmRecord:
    if isinstance(Value, KComplexTypes):
        return MakeComplex(Value)
    if isinstance(
        Value,
        (
            PointNode,
            PlaneNode,
            EllipseNode,
            ConeNode,
            StraightNode,
            TransformNode,
            SphereNode,
            TorusNode,
        ),
    ):
        return MakeCarriers(Value)
    if isinstance(
        Value,
        (
            TimeAttrib,
            TrackAttrib,
            TagAttrib,
            SketchAttrib,
            NestedTag,
            FeatureAttrib,
            NameAttrib,
        ),
    ):
        return MakeAttributes(Value)
    if isinstance(Value, StitchAttrib):
        return MakeStitchNode(Value)
    if isinstance(Value, NoMergeAttrib):
        return MakeNoMerge(Value)
    if isinstance(Value, VertedgeAttrib):
        return MakeVertedge(Value)
    return MakeTopology(Value)
