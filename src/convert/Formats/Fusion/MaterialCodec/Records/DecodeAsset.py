from convert.Formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.Formats.Fusion.MaterialCodec.Records.DecodeFields import DecodeFields
from convert.Formats.Fusion.MaterialCodec.Schema.SchemaTable import KSchemaTable
from convert.Formats.Fusion.MaterialCodec.Table.AssetEntry import AssetEntry
from convert.Formats.Fusion.MaterialCodec.Wire.MaterialReader import MaterialReader


# the asset operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
def DecodeAsset(
    Entry: AssetEntry, Definition: bytes, Instance: bytes, Schemas: KSchemaTable
) -> MaterialAsset:
    Reader = MaterialReader(Instance)
    SchemaName, InstanceId, DefinitionId = (Reader.ReadText() for _ in range(3))
    if SchemaName != Entry.SchemaName or InstanceId != Entry.InstanceId:
        raise ValueError("Fusion material instance header differs from its table entry")
    if SchemaName not in Schemas:
        raise ValueError("Missing Fusion material schema")
    Definitions = DecodeFields(MaterialReader(Definition), Schemas[SchemaName], True)
    Properties = DecodeFields(Reader, Schemas[SchemaName], False)
    return MaterialAsset(
        SchemaName, InstanceId, DefinitionId, Entry.AssetRole, Definitions, Properties
    )
