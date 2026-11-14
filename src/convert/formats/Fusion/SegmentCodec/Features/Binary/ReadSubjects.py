from struct import unpack as UnpackValue

from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureRefs
from convert.formats.Fusion.SegmentCodec.Features.Model.SubjectEntry import SubjectEntry
from convert.formats.Fusion.SegmentCodec.Features.Binary.ReadLocalRef import (
    ReadLocalRefMut,
)


def ReadSubjectsMut(Cursor: MetaCursor) -> tuple[SubjectEntry, ...]:
    Subjects: list[SubjectEntry] = []
    for _ in range(Cursor.ReadCount(KMaxFeatureRefs)):
        SubjectRef = ReadLocalRefMut(Cursor)
        ObserverIndex = int(UnpackValue("<i", Cursor.TakeBytes(4))[0])
        if SubjectRef is None or ObserverIndex < -1:
            raise ValueError("Invalid Fusion feature subject")
        Subjects.append(SubjectEntry(SubjectRef, ObserverIndex))
    return tuple(Subjects)
