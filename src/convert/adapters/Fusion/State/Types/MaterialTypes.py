from convert.formats.Fusion.MaterialCodec.Models.AssetLinks import AssetLinks
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue
from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from convert.formats.Fusion.MaterialCodec.Package.Model.PackageCore import PackageCore
from convert.formats.Fusion.MaterialCodec.Package.Model.ResourceInfo import ResourceInfo
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode

KMaterialTypes: tuple[type[object], ...] = (
    AssetLinks,
    ColorValue,
    MaterialAsset,
    PropertyValue,
    UnitValue,
    MaterialPackage,
    PackageCore,
    ResourceInfo,
    SchemaNode,
)
