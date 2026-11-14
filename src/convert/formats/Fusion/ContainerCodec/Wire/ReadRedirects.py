from convert.formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.formats.Fusion.BundleCodec.Json.ReadJson import ReadJson
from convert.formats.Fusion.ContainerCodec.Model.DocRedirects import DocRedirects
from convert.formats.Fusion.ContainerCodec.Model.RedirectDesign import RedirectDesign
from convert.formats.Fusion.ContainerCodec.Model.RedirectRef import RedirectRef
from convert.formats.Fusion.ContainerCodec.Wire.EmitRedirects import EmitRedirects

KStreamKeys = ("name", "schema-version", "designs", "references")

KDesignKeys = (
    "file-version",
    "targetFileName",
    "displayName",
    "lineageUrn",
    "versionUrn",
)

KReferKeys = ("from", "relativePath", "type", "properties")


def ReadDesignRow(Entry: KJsonValue) -> RedirectDesign:
    if not isinstance(Entry, dict) or tuple(Entry) != KDesignKeys:
        raise ValueError("Unsupported Fusion redirection design")
    Values = tuple(Entry[KeyName] for KeyName in KDesignKeys[1:])
    Version = Entry["file-version"]
    if type(Version) is not int or not all(
        isinstance(TextValue, str) for TextValue in Values
    ):
        raise ValueError("Unsupported Fusion redirection design")
    return RedirectDesign(
        Version, str(Values[0]), str(Values[1]), str(Values[2]), str(Values[3])
    )


def ReadReferRow(Entry: KJsonValue) -> RedirectRef:
    if not isinstance(Entry, dict) or tuple(Entry) != KReferKeys:
        raise ValueError("Unsupported Fusion redirection reference")
    SourceName, TargetName, Fields = Entry["from"], Entry["relativePath"], Entry["properties"]
    if (
        not isinstance(SourceName, str)
        or not isinstance(TargetName, str)
        or not isinstance(Fields, list)
    ):
        raise ValueError("Unsupported Fusion redirection reference")
    Properties: list[tuple[str, str]] = []
    for Field in Fields:
        if not isinstance(Field, dict) or len(Field) != 1:
            raise ValueError("Unsupported Fusion redirection reference property")
        ((KeyName, Inner),) = Field.items()
        if not isinstance(Inner, dict) or tuple(Inner) != ("value", "dataType"):
            raise ValueError("Unsupported Fusion redirection reference property")
        TextValue = Inner["value"]
        if not isinstance(TextValue, str):
            raise ValueError("Unsupported Fusion redirection reference property")
        Properties.append((KeyName, TextValue))
    return RedirectRef(SourceName, TargetName, tuple(Properties))


def ReadRedirects(Payload: bytes) -> DocRedirects:
    TreeValue = ReadJson(Payload)
    if not isinstance(TreeValue, dict) or tuple(TreeValue) != KStreamKeys:
        raise ValueError("Unsupported Fusion redirection stream")
    Designs, References = TreeValue["designs"], TreeValue["references"]
    if not isinstance(Designs, list) or not isinstance(References, (list, dict)):
        raise ValueError("Unsupported Fusion redirection stream")
    Result = DocRedirects(
        tuple(ReadDesignRow(Entry) for Entry in Designs),
        tuple(ReadReferRow(Entry) for Entry in References)
        if isinstance(References, list)
        else (),
    )
    if EmitRedirects(Result) != Payload:
        raise ValueError("Unsupported Fusion redirection stream encoding")
    return Result
