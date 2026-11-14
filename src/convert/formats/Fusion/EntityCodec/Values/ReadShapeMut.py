from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValueStruct import ValueStruct
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Recipes.ReadRecipeMut import ReadRecipeMut
from convert.formats.Fusion.EntityCodec.Schema.ClassGroups import ClassGroups
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Tags.ReadSketchMut import ReadSketchMut
from convert.formats.Fusion.EntityCodec.Values.ReadFieldsMut import ReadFieldsMut
from convert.formats.Fusion.EntityCodec.Values.ReadGroupsMut import ReadGroupsMut
from convert.formats.Fusion.EntityCodec.Values.ReadMatrixMut import ReadMatrixMut
from convert.formats.Fusion.EntityCodec.Values.ValueCalls import KReadValue
from convert.formats.Fusion.MetaCursor import MetaCursor


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
