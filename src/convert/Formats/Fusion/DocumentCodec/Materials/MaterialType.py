from convert.Formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.Formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


# the choice labels contract needs a shared interpretation so appearance references remain connected to their owning entities
def ChoiceLabels(Declared: SchemaNode) -> dict[str, int]:
    Labels: dict[str, int] = {}
    for Child in Declared.Children:
        if Child.TagName == "ChoiceValue":
            Attributes = dict(Child.Attributes)
            Labels[Attributes["label"]] = int(Attributes["val"])
    return Labels


# choice label needs an explicit validity boundary so appearance references remain connected to their owning entities
def ChoiceLabel(Declared: SchemaNode, Value: object) -> str:
    Found = tuple(
        LabelText
        for LabelText, Choice in ChoiceLabels(Declared).items()
        if Choice == Value
    )
    if len(Found) != 1:
        raise ValueError("Fusion material choice is not declared by its schema")
    return Found[0]


# choice input needs an explicit validity boundary so appearance references remain connected to their owning entities
def ChoiceInput(Fields: dict[str, SchemaNode], FieldName: str, LabelText: str) -> int:
    if FieldName not in Fields:
        raise ValueError("Material property has no place in its Fusion schema")
    Labels = ChoiceLabels(Fields[FieldName])
    if LabelText not in Labels:
        raise ValueError("Material choice is not declared by its Fusion schema")
    return Labels[LabelText]


# material type needs an explicit validity boundary so appearance references remain connected to their owning entities
def MaterialType(SpecValue: MaterialSpec, Declared: SchemaNode) -> int | None:
    Labels = ChoiceLabels(Declared)
    if SpecValue.TypeName is None:
        return Labels.get(SpecValue.ClassName)
    if SpecValue.TypeName not in Labels:
        raise ValueError("Material type is not declared by its Fusion schema")
    return Labels[SpecValue.TypeName]
