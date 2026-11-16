from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.SegmentCodec.Features.CheckLineage import CheckLineage
from convert.Formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureBytes
from convert.Formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.Formats.Fusion.SegmentCodec.Features.Model.FeatureRecord import (
    FeatureRecord,
)
from convert.Formats.Fusion.SegmentCodec.Features.RecordLayouts import RecordLayouts
from convert.Formats.Fusion.SegmentCodec.Features.Binary.ReadFrame import ReadFrameMut
from convert.Formats.Fusion.SegmentCodec.Features.Binary.ReadGroup import ReadGroupMut


# the feature operation needs a distinct decoding boundary so native records retain their segment ownership and schema
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
