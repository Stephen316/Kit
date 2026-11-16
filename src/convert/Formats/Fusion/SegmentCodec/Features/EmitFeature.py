from typing import cast as CastValue

from convert.Formats.Fusion.SegmentCodec.Features.CheckLineage import CheckLineage
from convert.Formats.Fusion.SegmentCodec.Features.Model.FeatureRecord import (
    FeatureRecord,
)
from convert.Formats.Fusion.SegmentCodec.Features.RecordLayouts import RecordLayouts
from convert.Formats.Fusion.SegmentCodec.Features.Binary.EmitFrame import EmitFrame
from convert.Formats.Fusion.SegmentCodec.Features.Binary.EmitGroup import EmitGroup
from convert.Formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


# the feature operation needs a consistent construction rule so native records retain their segment ownership and schema
def EmitFeature(Value: FeatureRecord) -> bytes:
    if not isinstance(CastValue(object, Value), FeatureRecord):
        raise ValueError("Invalid Fusion feature record")
    IsPrimary, Layouts = RecordLayouts(CheckLineage(Value.Lineage))
    if type(Value.Groups) is not tuple or len(Value.Groups) != len(Layouts):
        raise ValueError("Fusion feature member groups disagree with the class lineage")
    Output = FeatureSink()
    Output.AddBytes(EmitFrame(Value.Frame, IsPrimary))
    for Group, Layout in zip(Value.Groups, Layouts, strict=True):
        Output.AddBytes(EmitGroup(Group, Layout))
    return bytes(Output.Buffer)
