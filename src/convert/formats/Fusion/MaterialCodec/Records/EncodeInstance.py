from convert.formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec
from convert.formats.Fusion.MaterialCodec.Records.EncodeFields import EncodeFields
from convert.formats.Fusion.MaterialCodec.Wire.EncodeText import EncodeText


def EncodeInstance(Asset: MaterialAsset, Fields: tuple[PropertySpec, ...]) -> bytes:
    Header = b"".join(
        EncodeText(Value)
        for Value in (Asset.SchemaName, Asset.InstanceId, Asset.DefinitionId)
    )
    return Header + EncodeFields(Fields, Asset.Properties, False)
