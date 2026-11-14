from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.MaterialType import (
    ChoiceInput,
    MaterialType,
)
from convert.formats.Fusion.DocumentCodec.Materials.PlaceValue import PlaceValue
from convert.formats.Fusion.DocumentCodec.Materials.StoredValue import (
    KInputValue,
    StoredValue,
)
from convert.formats.Fusion.DocumentCodec.Materials.Vocabulary.FamilyFields import (
    KColorFields,
    KFinishFields,
    KInteriorModels,
    KMechanicFields,
    KThermalFields,
)
from convert.formats.Fusion.MaterialCodec.Models.AssetLinks import AssetLinks
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import PropertyValue
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


def PhysicalProps(
    SpecValue: MaterialSpec, Aspects: tuple[str, ...], Fields: dict[str, SchemaNode]
) -> tuple[PropertyValue, ...]:
    TypeValue = MaterialType(SpecValue, Fields["physmat_Type"])
    return (
        PropertyValue("physmat_Label", SpecValue.NameValue),
        *(() if TypeValue is None else (PropertyValue("physmat_Type", TypeValue),)),
        PropertyValue("physmat_aspects", None, AssetLinks(True, Aspects)),
    )


def SpecValues(
    Source: object, Mapping: dict[str, tuple[str, ...]]
) -> tuple[tuple[tuple[str, ...], KInputValue], ...]:
    Values: list[tuple[tuple[str, ...], KInputValue]] = []
    for FieldKey, Candidates in Mapping.items():
        Value = getattr(Source, FieldKey)
        if Value is not None:
            Values.append((Candidates, Value))
    return tuple(Values)


def PlaceAll(
    Fields: dict[str, SchemaNode],
    Values: tuple[tuple[tuple[str, ...], KInputValue], ...],
) -> tuple[PropertyValue, ...]:
    return tuple(
        Placed
        for Candidates, Value in Values
        for Placed in PlaceValue(Fields, Candidates, Value)
    )


def StructProps(
    SpecValue: MaterialSpec, Fields: dict[str, SchemaNode]
) -> tuple[PropertyValue, ...]:
    Mechanics = SpecValue.Mechanics
    Placed = {
        Entry.FieldName: Entry
        for Entry in PlaceAll(
            Fields,
            (
                (("structural_Density",), SpecValue.Density),
                *SpecValues(Mechanics, KMechanicFields),
            ),
        )
    }
    if Mechanics.Behavior is not None:
        Placed["structural_Behavior"] = PropertyValue(
            "structural_Behavior",
            ChoiceInput(Fields, "structural_Behavior", Mechanics.Behavior),
        )
    for Override in Mechanics.Directional:
        Target = KMechanicFields[Override.FieldKey][0] + "_" + Override.Direction
        if Target not in Fields:
            raise ValueError("Material direction has no place in its Fusion schema")
        Placed[Target] = PropertyValue(
            Target, StoredValue(Fields[Target], Override.Value)
        )
    return tuple(Placed.values())


def ThermalProps(
    SpecValue: MaterialSpec, Fields: dict[str, SchemaNode]
) -> tuple[PropertyValue, ...]:
    Thermal = SpecValue.Thermal
    if Thermal is None:
        raise ValueError("Thermal material aspect requires thermal values")
    Inherited: dict[str, float | None] = {
        "Density": SpecValue.Density,
        "Conductivity": SpecValue.Mechanics.Conductivity,
        "SpecificHeat": SpecValue.Mechanics.SpecificHeat,
    }
    Values: list[tuple[tuple[str, ...], KInputValue]] = []
    for FieldKey, Candidates in KThermalFields.items():
        Value = getattr(Thermal, FieldKey)
        Value = Inherited.get(FieldKey) if Value is None else Value
        if Value is not None:
            Values.append((Candidates, Value))
    return PlaceAll(Fields, tuple(Values))


def FinishProps(
    SpecValue: MaterialSpec, Fields: dict[str, SchemaNode], FinishLocal: str
) -> tuple[PropertyValue, ...]:
    Finish = SpecValue.Finish
    Values: list[tuple[tuple[str, ...], KInputValue]] = [
        (KColorFields, SpecValue.Color),
        (("interior_model",), KInteriorModels[FinishLocal]),
    ]
    if Finish.ColorSpace is not None:
        Values.extend(
            ((FieldKey,), Finish.ColorSpace)
            for FieldKey in sorted(Fields)
            if FieldKey.endswith("_colorspace")
        )
    Values.extend(SpecValues(Finish, KFinishFields))
    return PlaceAll(Fields, tuple(Values))
