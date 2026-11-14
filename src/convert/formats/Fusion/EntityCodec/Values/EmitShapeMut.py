from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Recipes.EmitRecipeMut import EmitRecipeMut
from convert.formats.Fusion.EntityCodec.Schema.ClassGroups import ClassGroups
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Tags.EmitSketchMut import EmitSketchMut
from convert.formats.Fusion.EntityCodec.Values.EmitFieldsMut import EmitFieldsMut
from convert.formats.Fusion.EntityCodec.Values.EmitGroupsMut import EmitGroupsMut
from convert.formats.Fusion.EntityCodec.Values.EmitMatrix import EmitMatrix
from convert.formats.Fusion.EntityCodec.Values.ValueCalls import KEmitValue


def EmitShapeMut(
    Value: KEntityValue,
    Shape: WireType,
    Catalog: EntityCatalog,
    Depth: int,
    Writer: KEmitValue,
) -> bytes:
    if Shape.KindValue == "struct" and isinstance(Value, ValueStruct):
        return EmitFieldsMut(Value.Fields, Shape.Members, Catalog, Depth, Writer)
    if Shape.KindValue == "object" and isinstance(Value, ValueObject):
        Groups = ClassGroups(Catalog, Shape.ClassGuid)
        if not any(Field.IsSaved for Group in Groups for Field in Group.Members):
            raise ValueError("Fusion value object has no qualified persisted fields")
        return EmitGroupsMut(Value.Groups, Groups, Catalog, Depth, Writer)
    if Shape.KindValue == "matrix":
        return EmitMatrix(Value, Shape)
    if Shape.KindValue == "recipe":
        return EmitRecipeMut(Value, Catalog, Depth)
    if Shape.KindValue == "sketch-tag":
        return EmitSketchMut(Value, Catalog, Depth, Writer)
    raise ValueError("Fusion entity value does not match its declared layout")
