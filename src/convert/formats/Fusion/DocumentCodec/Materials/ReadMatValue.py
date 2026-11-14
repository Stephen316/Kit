from convert.formats.Fusion.DocumentCodec.Materials.Vocabulary.MaterialUnits import (
    KMaterialUnits,
)
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import KMaterialValue
from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


def ReadMatValue(Value: SchemaNode) -> KMaterialValue:
    Attributes = dict(Value.Attributes)
    TextValue = Attributes.get("val", "")
    if Attributes.get("allowmultiplevalues") == "true":
        if TextValue:
            raise ValueError("Unsupported authored multi-value schema default")
        return ()
    if Value.TagName in ("String", "URL", "Uuid"):
        return TextValue
    if Value.TagName == "Boolean" and TextValue in ("true", "false"):
        return TextValue == "true"
    if Value.TagName == "Integer":
        return int(TextValue)
    if Value.TagName == "Choice":
        Choices = {
            dict(Child.Attributes)["id"]: dict(Child.Attributes)["val"]
            for Child in Value.Children
            if Child.TagName == "ChoiceValue"
        }
        return int(Choices[TextValue])
    if Value.TagName in ("Float", "Distance"):
        Magnitude = float(TextValue)
        UnitName = Attributes.get("unit")
        return (
            Magnitude
            if UnitName is None
            else UnitValue(KMaterialUnits[UnitName], Magnitude)
        )
    if Value.TagName == "Color":
        return ColorValue(
            *(float(Attributes["val" + Channel]) for Channel in ("R", "G", "B", "A"))
        )
    if Value.TagName == "Reference":
        return None
    raise ValueError("Unsupported authored material schema default")
