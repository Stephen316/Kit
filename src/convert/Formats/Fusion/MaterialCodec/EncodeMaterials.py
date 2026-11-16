from convert.Formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.Formats.Fusion.MaterialCodec.Models.MaterialData import MaterialData
from convert.Formats.Fusion.MaterialCodec.Models.MaterialSchema import MaterialSchema
from convert.Formats.Fusion.MaterialCodec.Records.CheckAssets import CheckAssets
from convert.Formats.Fusion.MaterialCodec.Records.EncodeFields import EncodeFields
from convert.Formats.Fusion.MaterialCodec.Records.EncodeInstance import EncodeInstance
from convert.Formats.Fusion.MaterialCodec.Schema.BuildSchemas import BuildSchemas
from convert.Formats.Fusion.MaterialCodec.Stores.EncodeStore import EncodeStore
from convert.Formats.Fusion.MaterialCodec.Table.EncodeTable import EncodeTable


# the materials operation needs a consistent construction rule so typed appearance properties retain their native identifiers
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
