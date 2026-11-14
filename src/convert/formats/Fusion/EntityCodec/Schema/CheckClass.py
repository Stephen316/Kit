from convert.formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.formats.Fusion.EntityCodec.Schema.CheckWireType import CheckWireType
from convert.formats.Fusion.EntityCodec.Schema.ClassGroups import ClassGroups
from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Wire.CheckFlag import CheckFlag
from convert.formats.Fusion.SegmentCodec.Features.Binary.EmitText import EmitText


def CheckClass(Schema: ClassSchema, Catalog: EntityCatalog) -> None:
    if not Schema.ClassGuid or not EmitText(Schema.ClassGuid):
        raise ValueError("Fusion entity class requires an identifier")
    _ = EmitText(Schema.BaseGuid)
    if type(Schema.SchemaVersion) is not int or not 0 <= Schema.SchemaVersion < 1 << 32:
        raise ValueError("Invalid Fusion entity schema version")
    CheckFlag(Schema.IsValue)
    CheckFlag(Schema.IsOpaque)
    if Schema.IsOpaque and (Schema.Members or Schema.IsValue):
        raise ValueError("Fusion opaque entity class must have no declared members")
    if len(Schema.Members) > KMaxCount:
        raise ValueError("Invalid Fusion entity class declaration")
    Names = tuple(Field.FieldName for Field in Schema.Members)
    if len(set(Names)) != len(Names) or not all(Names):
        raise ValueError("Duplicate or empty Fusion entity field identifier")
    if Schema.ClassGuid.upper() == Catalog.RootGuid and (
        Schema.Members or Schema.BaseGuid
    ):
        raise ValueError("Fusion entity root must have an empty declaration")
    _ = ClassGroups(Catalog, Schema.ClassGuid)
    for Field in Schema.Members:
        _ = EmitText(Field.FieldName)
        if type(Field.IsSaved) is not bool:
            raise ValueError("Fusion entity persistence flag must be boolean")
        CheckWireType(Field.ValueType, Catalog)
