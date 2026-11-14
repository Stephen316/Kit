from typing import cast as CastValue

from convert.formats.Fusion.MaterialCodec.Package.Model.ResourceInfo import ResourceInfo
from convert.formats.Fusion.MaterialCodec.Package.Validation.CheckTimestamp import (
    CheckTimestamp,
)


def CheckResources(
    Values: tuple[ResourceInfo, ...], Names: tuple[str, ...], ContentType: str
) -> None:
    if len(Values) != len(Names) or {Value.FileName for Value in Values} != set(Names):
        raise ValueError("Material resource links disagree with members")
    if len({Value.LinkName for Value in Values}) != len(Values):
        raise ValueError("Duplicate material resource link")
    for Value in Values:
        Expected = Value.FileName.rsplit(".", 1)[0]
        if (
            Value.LinkName != Expected
            or Value.ContentType != ContentType
            or type(CastValue(object, Value.IsInterop)) is not bool
            or Value.IsInterop
        ):
            raise ValueError("Unsupported material resource profile")
        CheckTimestamp(Value.Created)
