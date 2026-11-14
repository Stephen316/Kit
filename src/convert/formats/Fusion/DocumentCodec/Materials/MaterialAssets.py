from dataclasses import replace as ReplaceData

from convert.formats.Fusion.DocumentCodec.Materials.BuildMatAsset import BuildMatAsset
from convert.formats.Fusion.DocumentCodec.Materials.MatProperties import (
    FinishProps,
    PhysicalProps,
    StructProps,
    ThermalProps,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.AssetFamily import AssetFamily
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialIds import MaterialIds
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.PlanMaterial import PlanMaterial
from convert.formats.Fusion.DocumentCodec.Materials.SchemaFacts import SchemaFacts
from convert.formats.Fusion.DocumentCodec.Materials.SchemaFields import SchemaFields
from convert.formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode
from convert.formats.Fusion.MaterialCodec.Package.SchemaModels import SchemaModels


def IndexSchemas(Nodes: tuple[SchemaNode, ...]) -> dict[str, SchemaNode]:
    return {
        dict(Child.Attributes)["val"]: Declared
        for Declared in Nodes
        for Child in Declared.Children
        if Child.TagName == "UID"
    }


def MaterialAssets(
    SpecValue: MaterialSpec, Identity: MaterialIds, Nodes: tuple[SchemaNode, ...]
) -> tuple[MaterialAsset, ...]:
    Indexed = IndexSchemas(Nodes)
    PlanValue = PlanMaterial(SpecValue, Indexed)
    Finish = SpecValue.Finish
    Families = [
        MakeFamily(
            PlanValue.StructuralName,
            Identity.StructuralId,
            Identity.StructuralDef,
            SpecValue.NameValue + " Structural",
            StructProps(SpecValue, SchemaFields(PlanValue.StructuralName, Indexed)),
            Indexed,
        )
    ]
    if PlanValue.ThermalName is not None:
        Families.append(
            MakeFamily(
                PlanValue.ThermalName,
                Identity.ThermalId,
                Identity.ThermalDef,
                SpecValue.NameValue + " Thermal",
                ThermalProps(SpecValue, SchemaFields(PlanValue.ThermalName, Indexed)),
                Indexed,
            )
        )
    Families.append(
        MakeFamily(
            PlanValue.FinishName,
            Identity.AppearanceId,
            Identity.AppearanceDef,
            (
                SpecValue.NameValue + " Appearance"
                if Finish.NameValue is None
                else Finish.NameValue
            ),
            FinishProps(
                SpecValue,
                SchemaFields(PlanValue.FinishName, Indexed),
                PlanValue.FinishLocal,
            ),
            Indexed,
        )
    )
    Physical = MakeFamily(
        "PhysMatSchema",
        Identity.PhysicalId,
        Identity.PhysicalDef,
        SpecValue.NameValue,
        PhysicalProps(
            SpecValue,
            tuple(Family.InstanceId for Family in Families),
            SchemaFields("PhysMatSchema", Indexed),
        ),
        Indexed,
    )
    Schemas = SchemaModels(Nodes)
    Library = PropertyValue("AssetLibID", Identity.LibraryId)
    return tuple(
        BuildMatAsset(
            ReplaceData(Family, Properties=(Library, *Family.Properties)),
            Indexed,
            Schemas,
        )
        for Family in (Physical, *Families)
    )


def MakeFamily(
    SchemaName: str,
    InstanceId: str,
    DefinitionId: str,
    NameValue: str,
    Properties: tuple[PropertyValue, ...],
    Indexed: dict[str, SchemaNode],
) -> AssetFamily:
    AssetRole = SchemaFacts(Indexed[SchemaName])[0]
    if not AssetRole:
        raise ValueError("Fusion material schema declares no asset role")
    return AssetFamily(
        SchemaName, InstanceId, DefinitionId, AssetRole, NameValue, Properties
    )
