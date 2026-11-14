from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, SeriesItems
from convert.adapters.Fusion.Native.Graph.IntegerValue import IntegerValue
from convert.adapters.Fusion.Native.Rectangle.CurveTags import CurveTag, SketchTag
from convert.adapters.Fusion.Native.Rectangle.RectGeometry import RectGeometry
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


def CheckSideRecipe(Value: KEntityValue, Shape: RectGeometry) -> int:
    Fields = ObjectFields(Value)
    Values = SeriesItems(Fields["sketchTags"])
    if len(Values) != 1:
        raise ValueError("Native rectangular side requires one progenitor sketch tag")
    TagId = SketchTag(Values[0], 1)
    TagValues = tuple(CurveTag(NodeValue) for NodeValue in Shape.LineNodes)
    if TagId not in TagValues:
        raise ValueError("Native side progenitor does not belong to the sketch")
    Index = TagValues.index(TagId)
    ExpectedStart, ExpectedEnd = TagValues[(Index - 1) % 4], TagValues[(Index + 1) % 4]
    ActualStart = tuple(
        IntegerValue(ItemValue)
        for ItemValue in SeriesItems(Fields["startAdjacentPrimaryTagIds"])
    )
    ActualEnd = tuple(
        IntegerValue(ItemValue)
        for ItemValue in SeriesItems(Fields["endAdjacentPrimaryTagIds"])
    )
    if ActualStart != (ExpectedStart,) or ActualEnd != (ExpectedEnd,):
        raise ValueError(
            "Native side progenitor adjacency disagrees with sketch incidence"
        )
    return TagId
