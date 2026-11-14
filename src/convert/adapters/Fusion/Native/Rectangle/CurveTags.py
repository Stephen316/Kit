from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


def CurveTag(NodeValue: NativeNode) -> int:
    Metadata = {
        ItemValue.FieldName: ItemValue.Value
        for ItemValue in NodeValue.Frame.Metadata or ()
    }
    if Metadata.get("crv_secondary_id") != 0:
        raise ValueError("Native profile requires unsplit primary sketch tags")
    return IntegerValue(Metadata["crv_primary_id"])


def SketchTag(Value: KEntityValue, Direction: int) -> int:
    Fields = ObjectFields(Value)
    Expected = {
        "version": 3,
        "secondaryTagId": 0,
        "direction": Direction,
        "splitSequenceId": 1,
        "splitTotalNumber": 1,
        "topologyRoleFlags": 0,
    }
    if any(
        Fields.get(NameValue) != ItemValue for NameValue, ItemValue in Expected.items()
    ):
        raise ValueError("Unsupported native profile sketch tag")
    return IntegerValue(Fields["tagId"])
