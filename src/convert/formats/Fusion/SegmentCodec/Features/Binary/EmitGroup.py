from typing import cast as CastValue

from convert.formats.Fusion.SegmentCodec.Features.Model.FeatureField import FeatureField
from convert.formats.Fusion.SegmentCodec.Features.Model.FeatureGroup import FeatureGroup
from convert.formats.Fusion.SegmentCodec.Features.Model.FieldValue import KFieldValue
from convert.formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.PersistFields import (
    PersistFields,
)
from convert.formats.Fusion.SegmentCodec.Features.Binary.EmitField import EmitField
from convert.formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


def EmitGroup(Group: FeatureGroup, Layout: ClassLayout) -> bytes:
    if (
        not isinstance(CastValue(object, Group), FeatureGroup)
        or type(Group.ClassGuid) is not str
        or Group.ClassGuid.upper() != Layout.Stamp.ClassGuid.upper()
        or type(Group.Fields) is not tuple
        or len(Group.Fields) > len(Layout.Members)
    ):
        raise ValueError("Invalid Fusion feature member group")
    Values: dict[str, KFieldValue] = {}
    for Field in Group.Fields:
        if (
            not isinstance(CastValue(object, Field), FeatureField)
            or type(Field.NameText) is not str
            or Field.NameText in Values
        ):
            raise ValueError("Invalid or duplicate Fusion feature field")
        Values[Field.NameText] = Field.Value
    Members = PersistFields(Layout)
    if Values.keys() != {Member.NameText for Member in Members}:
        raise ValueError("Fusion feature fields disagree with the persisted schema")
    Output = FeatureSink()
    for Member in Members:
        Output.AddBytes(EmitField(Member.WireKind, Values[Member.NameText]))
    return bytes(Output.Buffer)
