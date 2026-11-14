from convert.formats.Fusion.BrepCodec.Journal.Attributes.FeatureAttrib import (
    FeatureAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeFdmAttrib import (
    MakeFdmAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeTimeAttrib import (
    MakeTimeAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeTrackAttrib import (
    MakeTrackAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeTagAttrib import (
    MakeTagAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeSketchAttr import (
    MakeSketchAttr,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.NestedTag import NestedTag
from convert.formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeNestedTag import (
    MakeNestedTag,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.NameAttrib import NameAttrib
from convert.formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeGenAttrib import (
    MakeNameNode,
)


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
