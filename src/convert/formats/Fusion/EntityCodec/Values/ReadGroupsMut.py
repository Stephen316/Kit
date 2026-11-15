from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Values.ReadFieldsMut import ReadFieldsMut
from convert.formats.Fusion.EntityCodec.Values.ValueCalls import KReadValue
from convert.formats.Fusion.MetaCursor import MetaCursor


# the groups operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
def ReadGroupsMut(
    Cursor: MetaCursor,
    Groups: tuple[ClassSchema, ...],
    Catalog: EntityCatalog,
    Depth: int,
    Reader: KReadValue,
) -> tuple[EntityGroup[KEntityValue], ...]:

    # ordering by field field name must stay deterministic so entity reconstruction resolves equivalent inputs consistently
    return tuple(
        (
            EntityGroup(
                Group.ClassGuid,
                (),
                Cursor.TakeBytes(len(Cursor.DataValue) - Cursor.Offset),
            )
            if Group.IsOpaque
            else EntityGroup(
                Group.ClassGuid,
                ReadFieldsMut(
                    Cursor,
                    tuple(sorted(Group.Members, key=lambda Field: Field.FieldName)),
                    Catalog,
                    Depth + 1,
                    Reader,
                ),
            )
        )
        for Group in Groups
    )
