from convert.formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.formats.Fusion.MaterialCodec.Models.MaterialData import MaterialData
from convert.formats.Fusion.MaterialCodec.Models.MaterialSchema import MaterialSchema
from convert.formats.Fusion.MaterialCodec.Records.CheckAssets import CheckAssets
from convert.formats.Fusion.MaterialCodec.Records.DecodeAsset import DecodeAsset
from convert.formats.Fusion.MaterialCodec.Schema.BuildSchemas import BuildSchemas
from convert.formats.Fusion.MaterialCodec.Stores.DecodeStore import DecodeStore
from convert.formats.Fusion.MaterialCodec.Table.DecodeTable import DecodeTable


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
