from convert.formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.formats.Fusion.MaterialCodec.Models.MaterialData import MaterialData
from convert.formats.Fusion.MaterialCodec.Models.MaterialSchema import MaterialSchema
from convert.formats.Fusion.MaterialCodec.Records.CheckAssets import CheckAssets
from convert.formats.Fusion.MaterialCodec.Records.EncodeFields import EncodeFields
from convert.formats.Fusion.MaterialCodec.Records.EncodeInstance import EncodeInstance
from convert.formats.Fusion.MaterialCodec.Schema.BuildSchemas import BuildSchemas
from convert.formats.Fusion.MaterialCodec.Stores.EncodeStore import EncodeStore
from convert.formats.Fusion.MaterialCodec.Table.EncodeTable import EncodeTable


def EncodeMaterials(
    Assets: tuple[MaterialAsset, ...], Schemas: tuple[MaterialSchema, ...]
) -> MaterialData:
    Resolved = BuildSchemas(Schemas)
    CheckAssets(Assets, Resolved)
    Definitions = EncodeStore(
        EncodeFields(Resolved[Asset.SchemaName], Asset.Definitions, True)
        for Asset in Assets
    )
    Instances = EncodeStore(
        EncodeInstance(Asset, Resolved[Asset.SchemaName]) for Asset in Assets
    )
    TableData = EncodeTable(Assets, Definitions.Roots, Instances.Roots)
    return MaterialData(TableData, Definitions.Payload, Instances.Payload)
