from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.Formats.Fusion.MaterialCodec.Package.Model.PackageCore import PackageCore
from convert.Formats.Fusion.MaterialCodec.Package.Model.PackageFolder import (
    PackageFolder,
)
from convert.Formats.Fusion.MaterialCodec.Package.Model.ResourceInfo import ResourceInfo
from convert.Formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


# material package needs an explicit state contract so typed appearance properties retain their native identifiers
@MakeDataClass(frozen=True, slots=True)
class MaterialPackage:
    RootCore: PackageCore
    AssetCore: PackageCore
    DataCore: PackageCore
    SchemaCore: PackageCore
    DataLinks: tuple[ResourceInfo, ...]
    SchemaLinks: tuple[ResourceInfo, ...]
    Schemas: tuple[SchemaNode, ...]
    Assets: tuple[MaterialAsset, ...]
    Resources: PackageFolder | None = None
