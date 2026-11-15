from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Materials.InputValue import InputValue
from convert.formats.Fusion.DocumentCodec.Materials.MaterialAssets import IndexSchemas
from convert.formats.Fusion.DocumentCodec.Materials.MaterialType import ChoiceLabel
from convert.formats.Fusion.DocumentCodec.Materials.Model.DirectionValue import (
    DirectionValue,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.FinishSpec import FinishSpec
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.MechanicSpec import (
    MechanicSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.ThermalSpec import (
    ThermalSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.ReadMatValue import ReadMatValue
from convert.formats.Fusion.DocumentCodec.Materials.SchemaFacts import SchemaFacts
from convert.formats.Fusion.DocumentCodec.Materials.SchemaFields import SchemaFields
from convert.formats.Fusion.DocumentCodec.Materials.StoredValue import KInputValue
from convert.formats.Fusion.DocumentCodec.Materials.Vocabulary.FamilyFields import (
    KColorFields,
    KDirections,
    KFinishFields,
    KMechanicFields,
    KThermalFields,
)
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import KMaterialValue
from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


# the asset view contract needs a dedicated boundary so appearance references remain connected to their owning entities
class AssetView:

    # asset view needs explicit initial state so appearance references remain connected to their owning entities
    def __init__(self, Asset: MaterialAsset, Indexed: dict[str, SchemaNode]) -> None:
        super().__init__()
        self.Asset = Asset
        self.Fields = SchemaFields(Asset.SchemaName, Indexed)
        self.Values: dict[str, KMaterialValue] = {
            Property.FieldName: Property.Value for Property in Asset.Properties
        }
        self.LocalValue = SchemaFacts(Indexed[Asset.SchemaName])[1]

    # the value operation needs a distinct decoding boundary so appearance references remain connected to their owning entities
    def ReadValue(self, Candidates: tuple[str, ...]) -> KInputValue | None:
        Present = tuple(Field for Field in Candidates if Field in self.Values)
        if len(Present) > 1:
            raise ValueError("Fusion material property has more than one place")
        if not Present:
            return None
        Declared = self.Fields[Present[0]]
        Value = self.Values[Present[0]]
        if Declared.TagName == "Distance" and Value == ReadMatValue(Declared):
            return None
        return InputValue(Declared, Value)


# the number operation needs a distinct decoding boundary so appearance references remain connected to their owning entities
def ReadNumber(Source: AssetView, Candidates: tuple[str, ...]) -> float | None:
    Value = Source.ReadValue(Candidates)
    if Value is None or type(Value) is float:
        return Value
    raise ValueError("Fusion material value is not a number")


# the flag operation needs a distinct decoding boundary so appearance references remain connected to their owning entities
def ReadFlag(Source: AssetView, Candidates: tuple[str, ...]) -> bool | None:
    Value = Source.ReadValue(Candidates)
    if Value is None or type(Value) is bool:
        return Value
    raise ValueError("Fusion material value is not a flag")


# the color operation needs a distinct decoding boundary so appearance references remain connected to their owning entities
def ReadColor(Source: AssetView, Candidates: tuple[str, ...]) -> ColorValue | None:
    Value = Source.ReadValue(Candidates)
    if Value is None or isinstance(Value, ColorValue):
        return Value
    raise ValueError("Fusion material value is not a color")


# the numbers operation needs a distinct decoding boundary so appearance references remain connected to their owning entities
def ReadNumbers(
    Source: AssetView,
    Mapping: dict[str, tuple[str, ...]],
    Skipped: tuple[str, ...] = (),
) -> dict[str, float | None]:
    return {
        FieldKey: ReadNumber(Source, Candidates)
        for FieldKey, Candidates in Mapping.items()
        if FieldKey not in Skipped
    }


# the choice operation needs a distinct decoding boundary so appearance references remain connected to their owning entities
def ReadChoice(Source: AssetView, FieldName: str) -> str | None:
    if FieldName not in Source.Values:
        return None
    return ChoiceLabel(Source.Fields[FieldName], Source.Values[FieldName])


# the steps operation needs a distinct decoding boundary so appearance references remain connected to their owning entities
def ReadSteps(Source: AssetView) -> tuple[DirectionValue, ...]:
    Steps: list[DirectionValue] = []
    for FieldKey, Candidates in KMechanicFields.items():
        MainName = Candidates[0]
        for Direction in KDirections:
            Target = MainName + "_" + Direction
            if Target not in Source.Values or MainName not in Source.Values:
                continue
            if Source.Values[Target] == Source.Values[MainName]:
                continue
            Value = ReadNumber(Source, (Target,))
            if Value is not None:
                Steps.append(DirectionValue(FieldKey, Direction, Value))
    return tuple(Steps)


# the mechanics operation needs a distinct decoding boundary so appearance references remain connected to their owning entities
def ReadMechanics(Source: AssetView) -> MechanicSpec:
    return MechanicSpec(
        **ReadNumbers(Source, KMechanicFields),
        Behavior=ReadChoice(Source, "structural_Behavior"),
        Directional=ReadSteps(Source),
    )


# project material needs an explicit validity boundary so appearance references remain connected to their owning entities
def ProjectMaterial(Package: MaterialPackage, PhysicalId: str) -> MaterialSpec:
    Indexed = IndexSchemas(Package.Schemas)
    Assets = {Asset.InstanceId: Asset for Asset in Package.Assets}
    Physical = Assets.get(PhysicalId)
    if Physical is None or Physical.SchemaName != "PhysMatSchema":
        raise ValueError("Fusion physical material asset is absent")
    Properties = {Entry.FieldName: Entry for Entry in Physical.Properties}
    Links = Properties["physmat_aspects"].Connections
    if Links is None or not Links.Enabled:
        raise ValueError("Fusion physical material has no enabled aspects")
    Roles: dict[str, AssetView] = {}
    for Target in Links.Targets:
        if Target not in Assets or Assets[Target].AssetRole in Roles:
            raise ValueError("Fusion material aspects are missing or repeated")
        Roles[Assets[Target].AssetRole] = AssetView(Assets[Target], Indexed)
    if "Structural" not in Roles or "materialappearance" not in Roles:
        raise ValueError("Fusion material lacks a structural or appearance aspect")
    Structural = Roles["Structural"]
    Appearance = Roles["materialappearance"]
    NameValue = Properties["physmat_Label"].Value
    Density = Structural.ReadValue(("structural_Density",))
    Color = Appearance.ReadValue(KColorFields)
    Spaces = {
        Value
        for FieldKey, Value in Appearance.Values.items()
        if FieldKey.endswith("_colorspace")
    }
    if (
        not isinstance(NameValue, str)
        or not isinstance(Density, float)
        or not isinstance(Color, ColorValue)
        or len(Spaces) > 1
    ):
        raise ValueError("Fusion material lacks a name, density, color or colorspace")
    Thermal = Roles.get("Thermal")
    Names = {Entry.FieldName: Entry.Value for Entry in Appearance.Asset.Definitions}
    Colors = ("Tint", "ScatterColor", "LayerColor")
    return MaterialSpec(
        NameValue,
        Density,
        Color,
        Structural.LocalValue,
        ReadMechanics(Structural),
        (
            None
            if Thermal is None
            else ThermalSpec(
                **ReadNumbers(Thermal, KThermalFields, ("TransmitsLight",)),
                TransmitsLight=ReadFlag(Thermal, KThermalFields["TransmitsLight"]),
            )
        ),
        FinishSpec(
            **ReadNumbers(Appearance, KFinishFields, (*Colors, "Translucent")),
            NameValue=CastValue(str, Names.get("UIName")),
            Metallic=Appearance.LocalValue == "Metal",
            ColorSpace=CastValue(int, next(iter(Spaces))) if Spaces else None,
            Tint=ReadColor(Appearance, KFinishFields["Tint"]),
            ScatterColor=ReadColor(Appearance, KFinishFields["ScatterColor"]),
            LayerColor=ReadColor(Appearance, KFinishFields["LayerColor"]),
            Translucent=ReadFlag(Appearance, KFinishFields["Translucent"]),
        ),
        ReadChoice(AssetView(Physical, Indexed), "physmat_Type"),
    )
