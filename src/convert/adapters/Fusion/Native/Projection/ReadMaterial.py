from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields, TextValue
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.formats.Fusion.DocumentCodec.Materials.Vocabulary.FamilyFields import (
    KColorFields,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Reading.Materials.ResolveMatAsset import (
    ResolveMatAsset,
)
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue
from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from interchange.materials.MaterialRecord import MaterialRecord


def ReadMaterial(
    Graph: NativeGraph, Context: ExtrudeContext, Model: DocumentModel
) -> MaterialRecord:
    Physical = ObjectFields(Context.BodyNode.Fields["physicalMaterial"])
    Visual = ObjectFields(Context.BodyNode.Fields["visualMaterial"])
    Manager = Graph.Resolve(Physical["ProteinAssetManager"])
    if (
        Graph.Resolve(Visual["ProteinAssetManager"]) != Manager
        or Visual["UseCustomizedColor"] is not False
    ):
        raise ValueError(
            "Native material projection requires shared package and asset appearance"
        )
    Parts = tuple(
        PartValue
        for PartValue in Model.Materials
        if PartValue.Name
        == "ProteinAssets.BlobParts/" + TextValue(Manager.Fields["partName"])
    )
    if len(Parts) != 1:
        raise ValueError("Native body material package is not unique")
    Package = Parts[0].Package
    Material = RequireAsset(Package, TextValue(Physical["assetReference"]))
    Appearance = RequireAsset(Package, TextValue(Visual["assetReference"]))
    Density = ReadDensity(Package, Material)
    Properties = {
        Property.FieldName: Property.Value for Property in Appearance.Properties
    }
    Colors = tuple(
        Properties[FieldKey] for FieldKey in KColorFields if FieldKey in Properties
    )
    Color = Colors[0] if len(Colors) == 1 else None
    Names = {Property.FieldName: Property.Value for Property in Material.Properties}
    Definitions = {
        Property.FieldName: Property.Value for Property in Material.Definitions
    }
    NameValue = Names.get("physmat_Label") or Definitions.get("UIName")
    if not isinstance(Color, ColorValue) or not isinstance(NameValue, str):
        raise ValueError(
            "Native material lacks qualified name or analytic appearance color"
        )
    return MaterialRecord(
        f"{Manager.Identity}:material:{Material.InstanceId}:{Appearance.InstanceId}",
        NameValue,
        Density,
        (Color.RedValue, Color.GreenValue, Color.BlueValue, Color.AlphaValue),
    )


def RequireAsset(Package: MaterialPackage, Identity: str) -> MaterialAsset:
    Asset = ResolveMatAsset(Package, Identity)
    if Asset is None:
        raise ValueError("Native material connection has no target")
    return Asset


def ReadDensity(Package: MaterialPackage, Material: MaterialAsset) -> float:
    Aspects = tuple(
        Property
        for Property in Material.Properties
        if Property.FieldName == "physmat_aspects"
    )
    if (
        len(Aspects) != 1
        or Aspects[0].Connections is None
        or not Aspects[0].Connections.Enabled
    ):
        raise ValueError("Native physical material has no enabled aspect connections")
    Densities = tuple(
        Property.Value
        for Identity in Aspects[0].Connections.Targets
        for Property in RequireAsset(Package, Identity).Properties
        if Property.FieldName == "structural_Density"
    )
    if (
        len(Densities) != 1
        or not isinstance(Densities[0], UnitValue)
        or Densities[0].UnitCode != 69633
        or Densities[0].Magnitude <= 0
    ):
        raise ValueError("Native physical material has no unique positive SI density")
    return Densities[0].Magnitude
