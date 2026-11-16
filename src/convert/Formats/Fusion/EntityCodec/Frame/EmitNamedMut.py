from convert.Formats.Fusion.EntityCodec.Frame.NamedShape import KVectorName, NamedShape
from convert.Formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.Formats.Fusion.EntityCodec.Model.NamedMetadata import NamedMetadata
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Values.EmitValueMut import EmitValueMut
from convert.Formats.Fusion.SegmentCodec.Features.Binary.EmitText import EmitText
from convert.Formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


# the named operation needs a consistent construction rule so entity identifiers retain their schema and reference meaning
def EmitNamedMut(Entries: tuple[NamedMetadata, ...], Catalog: EntityCatalog) -> bytes:
    if len({Entry.FieldName for Entry in Entries}) != len(Entries):
        raise ValueError("Duplicate Fusion entity named metadata")
    Output = FeatureSink()
    Output.AddCount(Entries, KMaxCount)
    for Entry in Entries:
        Shape = NamedShape(Entry.TypeName, Entry.ElementName, Catalog)
        Output.AddBytes(EmitText(Entry.FieldName))
        Output.AddBytes(EmitText(Entry.TypeName))
        if Entry.TypeName == KVectorName:
            Output.AddBytes(EmitText(Entry.ElementName))
        Output.AddBytes(EmitValueMut(Entry.Value, Shape, Catalog))
    return bytes(Output.Buffer)
