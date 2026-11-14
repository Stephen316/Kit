from uuid import UUID as UuidValue

from convert.formats.Fusion.MaterialCodec.Package.Model.PackageCore import PackageCore
from convert.formats.Fusion.MaterialCodec.Package.Validation.CheckTimestamp import (
    CheckTimestamp,
)


def CheckCore(Value: PackageCore) -> None:
    try:
        _ = UuidValue(Value.Identifier)
    except (ValueError, TypeError, AttributeError) as ErrorInfo:
        raise ValueError("Invalid material package identity") from ErrorInfo
    if (
        len(Value.Identifier) != 36
        or type(Value.Updates) is not int
        or not 0 <= Value.Updates <= 0xFFFFFFFF
    ):
        raise ValueError("Invalid material package metadata")
    CheckTimestamp(Value.Created)
    CheckTimestamp(Value.Updated)
    if Value.EmbedOption is not None and (
        type(Value.EmbedOption) is not int or Value.EmbedOption != 49
    ):
        raise ValueError("Unsupported material embed option")
    if Value.IsReadOnly is not None and type(Value.IsReadOnly) is not bool:
        raise ValueError("Invalid material read-only value")
    if any(
        TextValue is not None
        and (
            type(TextValue) is not str or len(TextValue) > 65536 or "\x00" in TextValue
        )
        for TextValue in (Value.NameValue, Value.LastSaved)
    ):
        raise ValueError("Invalid material core text")
