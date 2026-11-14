from convert.formats.Fusion.MaterialCodec.Package.PackageLimits import (
    KContentTypes,
    KPackageFormat,
    KTypeNamespace,
)
from convert.formats.Fusion.MaterialCodec.Package.Xml.CheckElement import CheckElement
from convert.formats.Fusion.MaterialCodec.Package.Xml.ParsePackageXml import (
    ParsePackageXml,
)


def CheckFormats(Types: bytes, Format: bytes) -> None:
    RootValue = ParsePackageXml(Types)
    CheckElement(RootValue, "{" + KTypeNamespace + "}Types", {})
    if len(RootValue) != len(KContentTypes):
        raise ValueError("Unsupported material content type count")
    Found: set[tuple[str, str]] = set()
    for Child in RootValue:
        Extension = Child.attrib.get("Extension", "")
        Content = Child.attrib.get("ContentType", "")
        CheckElement(
            Child,
            "{" + KTypeNamespace + "}Default",
            {"Extension": Extension, "ContentType": Content},
        )
        if len(Child) or (Extension, Content) in Found:
            raise ValueError("Invalid material content type declaration")
        Found.add((Extension, Content))
    if Found != set(KContentTypes):
        raise ValueError("Unsupported material content types")
    Formats = ParsePackageXml(Format)
    CheckElement(Formats, "formats", {})
    if len(Formats) != 1:
        raise ValueError("Unsupported material package format declarations")
    CheckElement(Formats[0], "format", {}, HasText=True)
    if len(Formats[0]) or Formats[0].text != KPackageFormat:
        raise ValueError("Unsupported material package format")
