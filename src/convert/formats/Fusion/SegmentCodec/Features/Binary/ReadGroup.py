from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Features.Model.FeatureField import FeatureField
from convert.formats.Fusion.SegmentCodec.Features.Model.FeatureGroup import FeatureGroup
from convert.formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.PersistFields import (
    PersistFields,
)
from convert.formats.Fusion.SegmentCodec.Features.Binary.ReadField import ReadFieldMut


def ReadGroupMut(Cursor: MetaCursor, Layout: ClassLayout) -> FeatureGroup:
    Fields = tuple(
        FeatureField(Field.NameText, ReadFieldMut(Cursor, Field.WireKind))
        for Field in PersistFields(Layout)
    )
    return FeatureGroup(Layout.Stamp.ClassGuid, Fields)
