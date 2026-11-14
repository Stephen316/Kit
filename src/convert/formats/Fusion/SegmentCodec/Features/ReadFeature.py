from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Features.CheckLineage import CheckLineage
from convert.formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureBytes
from convert.formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.formats.Fusion.SegmentCodec.Features.Model.FeatureRecord import (
    FeatureRecord,
)
from convert.formats.Fusion.SegmentCodec.Features.RecordLayouts import RecordLayouts
from convert.formats.Fusion.SegmentCodec.Features.Binary.ReadFrame import ReadFrameMut
from convert.formats.Fusion.SegmentCodec.Features.Binary.ReadGroup import ReadGroupMut


def ReadFeature(Payload: bytes, Lineage: tuple[ClassStamp, ...]) -> FeatureRecord:
    if type(Payload) is not bytes or len(Payload) > KMaxFeatureBytes:
        raise ValueError("Invalid or oversized Fusion feature payload")
    IsPrimary, Layouts = RecordLayouts(CheckLineage(Lineage))
    Cursor = MetaCursor(Payload)
    Frame = ReadFrameMut(Cursor, IsPrimary)
    Groups = tuple(ReadGroupMut(Cursor, Layout) for Layout in Layouts)
    if Cursor.Offset != len(Payload):
        raise ValueError("Unexplained trailing Fusion feature bytes")
    return FeatureRecord(Lineage, Frame, Groups)
