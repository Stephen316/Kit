from convert.formats.Fusion.MaterialCodec.Limits import KMaxCount
from convert.formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.formats.Fusion.MaterialCodec.Schema.SchemaTable import KSchemaTable
from convert.formats.Fusion.MaterialCodec.Wire.EncodeText import EncodeText


def CheckAssets(Assets: tuple[MaterialAsset, ...], Schemas: KSchemaTable) -> None:
    if not 1 <= len(Assets) <= KMaxCount:
        raise ValueError("Fusion material assets exceed the count limit")
    Identities = {Asset.InstanceId for Asset in Assets}
    if len(Identities) != len(Assets):
        raise ValueError("Duplicate Fusion material instance identifier")
    Definitions: dict[str, str] = {}
    for Asset in Assets:
        if Asset.SchemaName not in Schemas:
            raise ValueError("Missing Fusion material schema")
        for Value in (Asset.InstanceId, Asset.DefinitionId, Asset.AssetRole):
            if not Value or not EncodeText(Value):
                raise ValueError("Fusion material asset identity must not be empty")
        if (
            Definitions.setdefault(Asset.DefinitionId, Asset.SchemaName)
            != Asset.SchemaName
        ):
            raise ValueError("Conflicting Fusion material definition identity")
        for Entry in Asset.Properties:
            if Entry.Connections is not None:
                if any(
                    Target not in Identities for Target in Entry.Connections.Targets
                ):
                    raise ValueError("Fusion material connection target is missing")
