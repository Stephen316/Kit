from struct import pack as PackValue
from typing import cast as CastValue

from convert.formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureRefs
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.formats.Fusion.SegmentCodec.Features.Model.SubjectEntry import SubjectEntry
from convert.formats.Fusion.SegmentCodec.Features.Binary.EmitLocalRef import (
    EmitLocalRef,
)
from convert.formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


def EmitSubjects(Subjects: tuple[SubjectEntry, ...]) -> bytes:
    if type(Subjects) is not tuple or len(Subjects) > KMaxFeatureRefs:
        raise ValueError("Invalid Fusion feature subject list")
    Output = FeatureSink()
    Output.AddWord(len(Subjects))
    for Entry in Subjects:
        if (
            not isinstance(CastValue(object, Entry), SubjectEntry)
            or not isinstance(CastValue(object, Entry.SubjectRef), LocalRef)
            or type(Entry.ObserverIndex) is not int
            or not -1 <= Entry.ObserverIndex < 1 << 31
        ):
            raise ValueError("Invalid Fusion feature subject")
        Output.AddBytes(EmitLocalRef(Entry.SubjectRef))
        Output.AddBytes(PackValue("<i", Entry.ObserverIndex))
    return bytes(Output.Buffer)
