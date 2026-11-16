from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.Formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.EntityCodec.Recipes.ReadRecipeMut import ReadRecipeMut
from convert.Formats.Fusion.EntityCodec.Schema.ClassGroups import ClassGroups
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Tags.ReadSketchMut import ReadSketchMut
from convert.Formats.Fusion.EntityCodec.Values.ReadFieldsMut import ReadFieldsMut
from convert.Formats.Fusion.EntityCodec.Values.ReadGroupsMut import ReadGroupsMut
from convert.Formats.Fusion.EntityCodec.Values.ReadMatrixMut import ReadMatrixMut
from convert.Formats.Fusion.EntityCodec.Values.ValueCalls import KReadValue
from convert.Formats.Fusion.MetaCursor import MetaCursor


# the shape operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
def ReadShapeMut(
    Cursor: MetaCursor,
    Shape: WireType,
    Catalog: EntityCatalog,
    Depth: int,
    Reader: KReadValue,
) -> KEntityValue:
    if Shape.KindValue == "struct":
        return ValueStruct(ReadFieldsMut(Cursor, Shape.Members, Catalog, Depth, Reader))
    if Shape.KindValue == "object":
        Groups = ClassGroups(Catalog, Shape.ClassGuid)
        if not any(Field.IsSaved for Group in Groups for Field in Group.Members):
            raise ValueError("Fusion value object has no qualified persisted fields")
        return ValueObject(ReadGroupsMut(Cursor, Groups, Catalog, Depth, Reader))
    if Shape.KindValue == "matrix":
        return ReadMatrixMut(Cursor, Shape)
    if Shape.KindValue == "recipe":
        return ReadRecipeMut(Cursor, Catalog, Depth)
    if Shape.KindValue == "sketch-tag":
        return ReadSketchMut(Cursor, Catalog, Depth, Reader)
    raise ValueError("Unsupported Fusion entity value layout")
