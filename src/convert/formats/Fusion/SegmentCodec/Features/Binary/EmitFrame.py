from struct import pack as PackValue
from typing import cast as CastValue

from convert.formats.Fusion.SegmentCodec.Features.Model.FeatureFrame import FeatureFrame
from convert.formats.Fusion.SegmentCodec.Features.Binary.EmitSubjects import (
    EmitSubjects,
)
from convert.formats.Fusion.SegmentCodec.Features.Binary.EmitText import EmitText
from convert.formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


def EmitFrame(Frame: FeatureFrame, IsPrimary: bool) -> bytes:
    if (
        not isinstance(CastValue(object, Frame), FeatureFrame)
        or type(Frame.HasNamedMeta) is not bool
    ):
        raise ValueError("Invalid Fusion feature frame")
    Output = FeatureSink()
    Output.AddBytes(EmitText(Frame.RootId))
    if not IsPrimary:
        if Frame.Subjects is not None or Frame.HasNamedMeta:
            raise ValueError(
                "Fusion feature continuation has no subject or named metadata frame"
            )
        return bytes(Output.Buffer)
    Output.AddBytes(PackValue("<B", Frame.Subjects is not None))
    if Frame.Subjects is not None:
        Output.AddBytes(EmitSubjects(Frame.Subjects))
    Output.AddBytes(PackValue("<B", Frame.HasNamedMeta))
    if Frame.HasNamedMeta:
        Output.AddWord(0)
    return bytes(Output.Buffer)
