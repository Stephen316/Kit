from convert.Formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.Formats.Fusion.MaterialCodec.Models.MaterialData import MaterialData
from convert.Formats.Fusion.MaterialCodec.Models.MaterialSchema import MaterialSchema
from convert.Formats.Fusion.MaterialCodec.Records.CheckAssets import CheckAssets
from convert.Formats.Fusion.MaterialCodec.Records.DecodeAsset import DecodeAsset
from convert.Formats.Fusion.MaterialCodec.Schema.BuildSchemas import BuildSchemas
from convert.Formats.Fusion.MaterialCodec.Stores.DecodeStore import DecodeStore
from convert.Formats.Fusion.MaterialCodec.Table.DecodeTable import DecodeTable


# the materials operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
def DecodeMaterials(
    Streams: MaterialData, Schemas: tuple[MaterialSchema, ...]
) -> tuple[MaterialAsset, ...]:
    Resolved = BuildSchemas(Schemas)
    Entries = DecodeTable(Streams.TableData)
    Definitions = DecodeStore(
        Streams.DefinitionData, tuple(Entry.DefinitionRoot for Entry in Entries)
    )
    Instances = DecodeStore(
        Streams.InstanceData, tuple(Entry.InstanceRoot for Entry in Entries)
    )
    Assets = tuple(
        DecodeAsset(Entry, Definition, Instance, Resolved)
        for Entry, Definition, Instance in zip(
            Entries, Definitions, Instances, strict=True
        )
    )
    CheckAssets(Assets, Resolved)
    return Assets
