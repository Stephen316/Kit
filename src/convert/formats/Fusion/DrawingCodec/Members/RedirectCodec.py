from typing import cast as CastValue

from convert.formats.Fusion.BundleCodec.Json.EmitJson import EmitJson
from convert.formats.Fusion.BundleCodec.Json.JsonScalar import JsonInteger, JsonString
from convert.formats.Fusion.BundleCodec.Json.JsonShape import JsonArray, JsonObject
from convert.formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.formats.Fusion.BundleCodec.Json.ReadJson import ReadJson
from convert.formats.Fusion.DrawingCodec.Members.Redirections import (
    RedirectDesign,
    RedirectLink,
    Redirections,
    RedirectValue,
)

KStreamName = "RedirectionsStream"


def EmitRedirects(Value: Redirections) -> bytes:
    if not isinstance(CastValue(object, Value), Redirections):
        raise ValueError("Expected typed Fusion drawing redirections")
    Designs: list[KJsonValue] = [
        {
            "file-version": Entry.FileVersion,
            "targetFileName": Entry.TargetFile,
            "displayName": Entry.DisplayName,
            "lineageUrn": Entry.LineageUrn,
            "versionUrn": Entry.VersionUrn,
        }
        for Entry in Value.Designs
    ]
    Links: list[KJsonValue] = [
        {
            "from": Entry.Source,
            "relativePath": Entry.Target,
            "type": Entry.Kind,
            "properties": [
                {
                    ItemValue.Name: {
                        "value": ItemValue.Value,
                        "dataType": ItemValue.DataType,
                    }
                }
                for ItemValue in Entry.Properties
            ],
        }
        for Entry in Value.References
    ]
    return EmitJson(
        {
            "name": KStreamName,
            "schema-version": Value.SchemaVersion,
            "designs": Designs,
            "references": Links,
        }
    )


def ReadRedirects(Payload: bytes) -> Redirections:
    Fields = JsonObject(ReadJson(Payload), "name schema-version designs references")
    if Fields["name"] != KStreamName:
        raise ValueError("Unsupported Fusion drawing redirection stream")
    Result = Redirections(
        JsonInteger(Fields["schema-version"]),
        tuple(ReadDesign(Entry) for Entry in JsonArray(Fields["designs"])),
        tuple(ReadLink(Entry) for Entry in JsonArray(Fields["references"])),
    )
    if EmitRedirects(Result) != Payload:
        raise ValueError("Fusion drawing redirection stream is not canonical")
    return Result


def ReadDesign(Value: KJsonValue) -> RedirectDesign:
    Fields = JsonObject(
        Value, "file-version targetFileName displayName lineageUrn versionUrn"
    )
    return RedirectDesign(
        JsonInteger(Fields["file-version"]),
        JsonString(Fields["targetFileName"]),
        JsonString(Fields["displayName"]),
        JsonString(Fields["lineageUrn"]),
        JsonString(Fields["versionUrn"]),
    )


def ReadLink(Value: KJsonValue) -> RedirectLink:
    Fields = JsonObject(Value, "from relativePath type properties")
    Properties: list[RedirectValue] = []
    for Entry in JsonArray(Fields["properties"]):
        if not isinstance(Entry, dict) or len(Entry) != 1:
            raise ValueError("Unsupported Fusion drawing redirection property")
        NameValue, ItemValue = next(iter(Entry.items()))
        Typed = JsonObject(ItemValue, "value dataType")
        Properties.append(
            RedirectValue(
                NameValue, JsonString(Typed["value"]), JsonString(Typed["dataType"])
            )
        )
    return RedirectLink(
        JsonString(Fields["from"]),
        JsonString(Fields["relativePath"]),
        JsonString(Fields["type"]),
        tuple(Properties),
    )
