from convert.Formats.Fusion.BrepCodec.Journal.Attributes.FeatureAttrib import (
    FeatureAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeFdmAttrib import (
    MakeFdmAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeTimeAttrib import (
    MakeTimeAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeTrackAttrib import (
    MakeTrackAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeTagAttrib import (
    MakeTagAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeSketchAttr import (
    MakeSketchAttr,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.NestedTag import NestedTag
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeNestedTag import (
    MakeNestedTag,
)
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.NameAttrib import NameAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeGenAttrib import (
    MakeNameNode,
)


# the attributes operation needs a consistent construction rule so revision ownership survives native history reconstruction
def MakeAttributes(Value: KJournalEntity) -> AsmRecord:
    if isinstance(Value, TimeAttrib):
        return MakeTimeAttrib(Value)
    if isinstance(Value, TrackAttrib):
        return MakeTrackAttrib(Value)
    if isinstance(Value, TagAttrib):
        return MakeTagAttrib(Value)
    if isinstance(Value, SketchAttrib):
        return MakeSketchAttr(Value)
    if isinstance(Value, NestedTag):
        return MakeNestedTag(Value)
    if isinstance(Value, FeatureAttrib):
        return MakeFdmAttrib(Value)
    if isinstance(Value, NameAttrib):
        return MakeNameNode(Value)
    raise ValueError("Unsupported Fusion journal entity variant")
