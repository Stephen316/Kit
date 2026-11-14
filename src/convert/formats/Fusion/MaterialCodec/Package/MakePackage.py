from convert.formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from convert.formats.Fusion.MaterialCodec.Package.Model.PackageCore import PackageCore
from convert.formats.Fusion.MaterialCodec.Package.Model.ResourceInfo import ResourceInfo
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode
from convert.formats.Fusion.MaterialCodec.Package.PackageLimits import KStreamNames
from convert.formats.Fusion.MaterialCodec.Package.Schema.SchemaIdentity import (
    SchemaIdentity,
)
from convert.formats.Fusion.MaterialCodec.Package.Validation.CheckPackage import (
    CheckPackage,
)


def MakePackage(
    PackageId: str,
    AssetId: str,
    Timestamp: str,
    Schemas: tuple[SchemaNode, ...],
    Assets: tuple[MaterialAsset, ...],
) -> MaterialPackage:
    SchemaNames = tuple(SchemaIdentity(Value) + ".xml" for Value in Schemas)
    Result = MaterialPackage(
        PackageCore(PackageId, Timestamp, Timestamp, 1, LastSaved="", IsReadOnly=False),
        PackageCore(AssetId, Timestamp, Timestamp, 1, AssetId, 49),
        PackageCore(PackageId, Timestamp, Timestamp, 1, "AssetData"),
        PackageCore(PackageId, Timestamp, Timestamp, 1, "Schemas"),
        tuple(
            ResourceInfo(
                NameValue.rsplit(".", 1)[0],
                NameValue,
                "application/octet-stream",
                Timestamp,
            )
            for NameValue in KStreamNames
        ),
        tuple(
            ResourceInfo(
                NameValue.rsplit(".", 1)[0], NameValue, "application/xml", Timestamp
            )
            for NameValue in SchemaNames
        ),
        Schemas,
        Assets,
    )
    CheckPackage(Result)
    return Result
