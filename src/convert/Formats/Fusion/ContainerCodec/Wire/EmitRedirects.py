from typing import cast as CastValue

from convert.Formats.Fusion.BundleCodec.Json.EmitJson import EmitJson
from convert.Formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.Formats.Fusion.ContainerCodec.Model.DocRedirects import DocRedirects
from convert.Formats.Fusion.ContainerCodec.Model.RedirectDesign import RedirectDesign
from convert.Formats.Fusion.ContainerCodec.Model.RedirectRef import RedirectRef

# redirect label must remain consistent across callers so archive members retain their native ownership and reference relationships
KRedirectLabel = "RedirectionsStream"

# redirect kind must remain consistent across callers so archive members retain their native ownership and reference relationships
KRedirectKind = "XREF"

# redirect type must remain consistent across callers so archive members retain their native ownership and reference relationships
KRedirectType = "STRING"


# design tree needs an explicit validity boundary so archive members retain their native ownership and reference relationships
def DesignTree(Value: RedirectDesign) -> dict[str, KJsonValue]:
    if (
        not isinstance(CastValue(object, Value), RedirectDesign)
        or type(Value.FileVersion) is not int
        or not 0 < Value.FileVersion < 1 << 31
        or any(
            type(TextValue) is not str or not TextValue
            for TextValue in (
                Value.TargetName,
                Value.DisplayName,
                Value.LineageUrn,
                Value.VersionUrn,
            )
        )
    ):
        raise ValueError("Invalid Fusion redirection design")
    return {
        "file-version": Value.FileVersion,
        "targetFileName": Value.TargetName,
        "displayName": Value.DisplayName,
        "lineageUrn": Value.LineageUrn,
        "versionUrn": Value.VersionUrn,
    }


# refer tree needs an explicit validity boundary so archive members retain their native ownership and reference relationships
def ReferTree(Value: RedirectRef) -> dict[str, KJsonValue]:
    if (
        not isinstance(CastValue(object, Value), RedirectRef)
        or type(Value.SourceName) is not str
        or type(Value.TargetName) is not str
        or not Value.SourceName
        or not Value.TargetName
        or type(Value.Properties) is not tuple
    ):
        raise ValueError("Invalid Fusion redirection reference")
    Fields: list[KJsonValue] = []
    for Entry in Value.Properties:
        if (
            type(Entry) is not tuple
            or len(CastValue(tuple[object, ...], Entry)) != 2
            or type(Entry[0]) is not str
            or type(Entry[1]) is not str
            or not Entry[0]
        ):
            raise ValueError("Invalid Fusion redirection reference property")
        Fields.append({Entry[0]: {"value": Entry[1], "dataType": KRedirectType}})
    return {
        "from": Value.SourceName,
        "relativePath": Value.TargetName,
        "type": KRedirectKind,
        "properties": Fields,
    }


# the redirects operation needs a consistent construction rule so archive members retain their native ownership and reference relationships
def EmitRedirects(Value: DocRedirects) -> bytes:
    if (
        not isinstance(CastValue(object, Value), DocRedirects)
        or type(Value.Designs) is not tuple
        or type(Value.References) is not tuple
        or not Value.Designs
    ):
        raise ValueError("Invalid Fusion redirection stream")
    Designs: list[KJsonValue] = [DesignTree(Entry) for Entry in Value.Designs]
    References: KJsonValue = {}
    if Value.References:
        References = [ReferTree(Entry) for Entry in Value.References]
    return EmitJson(
        {
            "name": KRedirectLabel,
            "schema-version": 0,
            "designs": Designs,
            "references": References,
        }
    )
