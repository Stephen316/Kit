from convert.Formats.Fusion.MaterialCodec.Models.AssetLinks import AssetLinks
from convert.Formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.Formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.Formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.Formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue
from convert.Formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from convert.Formats.Fusion.MaterialCodec.Package.Model.PackageCore import PackageCore
from convert.Formats.Fusion.MaterialCodec.Package.Model.ResourceInfo import ResourceInfo
from convert.Formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode

# the material types order must stay explicit so public document claims remain grounded in native records
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
