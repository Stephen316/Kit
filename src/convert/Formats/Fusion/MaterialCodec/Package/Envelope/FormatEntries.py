from xml.etree.ElementTree import Element as XmlElement, SubElement

from convert.Formats.Fusion.MaterialCodec.Package.PackageLimits import (
    KContentTypes,
    KPackageFormat,
    KTypeNamespace,
)
from convert.Formats.Fusion.MaterialCodec.Package.Xml.EmitPackageXml import (
    EmitPackageXml,
)
from convert.Formats.Fusion.MaterialCodec.Package.Xml.TextElement import TextElement


# the format entries contract needs a shared interpretation so typed appearance properties retain their native identifiers
def FormatEntries() -> dict[str, bytes]:
    Types = XmlElement("Types", {"xmlns": KTypeNamespace})
    for Extension, ContentType in KContentTypes:
        _ = SubElement(
            Types, "Default", {"Extension": Extension, "ContentType": ContentType}
        )
    Formats = XmlElement("formats")
    Formats.append(TextElement("format", {}, KPackageFormat))
    return {
        "[Content_Types].xml": EmitPackageXml(Types),
        "autodesk-design-package.xml": EmitPackageXml(Formats),
    }
