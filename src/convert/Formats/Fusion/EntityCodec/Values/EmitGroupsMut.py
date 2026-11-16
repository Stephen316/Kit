from convert.Formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Values.EmitFieldsMut import EmitFieldsMut
from convert.Formats.Fusion.EntityCodec.Values.ValueCalls import KEmitValue
from convert.Formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


# the groups operation needs a consistent construction rule so entity identifiers retain their schema and reference meaning
def EmitGroupsMut(
    Values: tuple[EntityGroup[KEntityValue], ...],
    Groups: tuple[ClassSchema, ...],
    Catalog: EntityCatalog,
    Depth: int,
    Writer: KEmitValue,
) -> bytes:
    if len(Values) != len(Groups):
        raise ValueError("Fusion entity inherited group count differs from its schema")
    Output = FeatureSink()
    for Value, Group in zip(Values, Groups, strict=True):
        if Value.ClassGuid.upper() != Group.ClassGuid.upper():
            raise ValueError(
                "Fusion entity inherited group identity differs from its schema"
            )
        if Group.IsOpaque != (Value.Opaque is not None) or (
            Value.Opaque is not None and Value.Fields
        ):
            raise ValueError("Fusion entity opaque group differs from its schema")
        if Value.Opaque is not None:
            Output.AddBytes(Value.Opaque)
            continue

        # ordering by field field name must stay deterministic so entity reconstruction resolves equivalent inputs consistently
        Fields = tuple(sorted(Group.Members, key=lambda Field: Field.FieldName))
        Output.AddBytes(EmitFieldsMut(Value.Fields, Fields, Catalog, Depth + 1, Writer))
    return bytes(Output.Buffer)
