from typing import TypeAlias

from convert.formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.formats.Fusion.EntityCodec.Model.GeometryArray import GeometryArray
from convert.formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue

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
