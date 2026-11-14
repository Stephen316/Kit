from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from convert.formats.Fusion.MaterialCodec.Package.Validation.CheckCore import CheckCore


def CheckCoreRoles(Value: MaterialPackage) -> None:
    for CoreValue in (
        Value.RootCore,
        Value.AssetCore,
        Value.DataCore,
        Value.SchemaCore,
    ):
        CheckCore(CoreValue)
    RootValue, Asset = Value.RootCore, Value.AssetCore
    if (
        RootValue.NameValue is not None
        or RootValue.EmbedOption is not None
        or RootValue.LastSaved is None
        or RootValue.IsReadOnly is None
    ):
        raise ValueError("Unsupported root material metadata profile")
    if (
        Asset.NameValue != Asset.Identifier
        or Asset.EmbedOption != 49
        or Asset.LastSaved is not None
        or Asset.IsReadOnly is not None
    ):
        raise ValueError("Unsupported asset material metadata profile")
    for CoreValue, NameValue in (
        (Value.DataCore, "AssetData"),
        (Value.SchemaCore, "Schemas"),
    ):
        if (
            CoreValue.NameValue != NameValue
            or CoreValue.EmbedOption is not None
            or CoreValue.LastSaved is not None
            or CoreValue.IsReadOnly is not None
        ):
            raise ValueError("Unsupported material folder metadata profile")
