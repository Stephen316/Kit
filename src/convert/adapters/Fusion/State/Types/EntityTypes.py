from convert.Formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.Formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Model.GeometryArray import GeometryArray
from convert.Formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.Formats.Fusion.EntityCodec.Model.NamedMetadata import NamedMetadata
from convert.Formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.Formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.Formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.Formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.Formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.Formats.Fusion.EntityCodec.Recipes.Model.BaseRecipe import BaseRecipe
from convert.Formats.Fusion.EntityCodec.Recipes.Model.BodyRecipe import BodyRecipe
from convert.Formats.Fusion.EntityCodec.Recipes.Model.BoundFaceRecipe import (
    BoundFaceRecipe,
)
from convert.Formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from convert.Formats.Fusion.EntityCodec.Recipes.Model.FaceRecipe import FaceRecipe
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeTag import RecipeTag
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.Formats.Fusion.EntityCodec.Recipes.Model.UvOrder import UvOrder
from convert.Formats.Fusion.EntityCodec.Recipes.Model.UvOrderEntry import UvOrderEntry
from convert.Formats.Fusion.EntityCodec.Recipes.Model.VertexRecipe import VertexRecipe
from convert.Formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.Formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from convert.Formats.Fusion.EntityCodec.Schema.NamedType import NamedType
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType

# the entity types order must stay explicit so public document claims remain grounded in native records
KEntityTypes: tuple[type[object], ...] = (
    EntityFrame,
    EntityGroup,
    EntityRecord,
    GeometryArray,
    MatrixValue,
    NamedMetadata,
    NamedValue,
    OptionalValue,
    SegmentRef,
    SubjectValue,
    ValueMap,
    ValueObject,
    ValuePair,
    ValueSeries,
    ValueStruct,
    BaseRecipe,
    BodyRecipe,
    BoundFaceRecipe,
    EdgeRecipe,
    FaceRecipe,
    RecipeTag,
    RecipeValue,
    UvOrder,
    UvOrderEntry,
    VertexRecipe,
    ClassSchema,
    EntityProfile,
    ExternalTarget,
    FieldSpec,
    NamedType,
    WireType,
)
