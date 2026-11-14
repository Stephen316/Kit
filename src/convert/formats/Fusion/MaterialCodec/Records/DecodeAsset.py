from convert.formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.formats.Fusion.MaterialCodec.Records.DecodeFields import DecodeFields
from convert.formats.Fusion.MaterialCodec.Schema.SchemaTable import KSchemaTable
from convert.formats.Fusion.MaterialCodec.Table.AssetEntry import AssetEntry
from convert.formats.Fusion.MaterialCodec.Wire.MaterialReader import MaterialReader


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
