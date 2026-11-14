from convert.formats.Fusion.MaterialCodec.Package.Envelope.CoreTypes import KCoreTypes
from convert.formats.Fusion.MaterialCodec.Package.Model.PackageCore import PackageCore
from convert.formats.Fusion.MaterialCodec.Package.Validation.CheckCore import CheckCore
from convert.formats.Fusion.MaterialCodec.Package.Xml.CheckElement import CheckElement
from convert.formats.Fusion.MaterialCodec.Package.Xml.ReadFields import ReadFields
from convert.formats.Fusion.MaterialCodec.Package.Xml.ReadGroup import ReadGroup


def ReadCore(Payload: bytes) -> PackageCore:
    Group = ReadGroup(Payload, "content")
    if len(Group) != 1:
        raise ValueError("Material core requires one asset node")
    CheckElement(
        Group[0], "node", {"name": "asset", "class": "schema.autodesk.package.1.asset"}
    )
    Fields = ReadFields(Group[0], KCoreTypes)
    if not {
        "identifier",
        "created",
        "updated",
        "updates",
    } <= Fields.keys() or Fields.get("read only", "0") not in ("0", "1"):
        raise ValueError("Invalid material core fields")
    try:
        Result = PackageCore(
            Fields["identifier"],
            Fields["created"],
            Fields["updated"],
            int(Fields["updates"]),
            Fields.get("name"),
            int(Fields["embed option"]) if "embed option" in Fields else None,
            Fields.get("last saved"),
            Fields["read only"] == "1" if "read only" in Fields else None,
        )
    except ValueError as ErrorInfo:
        raise ValueError("Invalid material core integer") from ErrorInfo
    CheckCore(Result)
    return Result
