from typing import TypeAlias

from convert.Formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.Formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.Formats.Fusion.EntityCodec.Model.GeometryArray import GeometryArray
from convert.Formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.Formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.Formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue

# the entity value variants need one shared contract so entity reconstruction cannot omit a supported value shape
KEntityValue: TypeAlias = (  # lgtm[py/unused-global-variable]
    None
    | bool
    | int
    | float
    | str
    | LocalRef
    | SegmentRef
    | CrossRef
    | ValueSeries["KEntityValue"]
    | ValuePair["KEntityValue"]
    | ValueMap["KEntityValue"]
    | ValueStruct["KEntityValue"]
    | ValueObject["KEntityValue"]
    | MatrixValue
    | OptionalValue["KEntityValue"]
    | GeometryArray["KEntityValue"]
    | RecipeValue
)
