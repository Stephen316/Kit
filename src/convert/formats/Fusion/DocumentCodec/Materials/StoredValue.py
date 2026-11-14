from math import isfinite as IsFinite

from convert.formats.Fusion.DocumentCodec.Materials.Vocabulary.MaterialUnits import (
    KMaterialUnits,
    KUnitScales,
)
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import KScalarValue
from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode

KInputValue = float | bool | int | ColorValue


def StoredValue(Declared: SchemaNode, Value: KInputValue) -> KScalarValue:
    Attributes = dict(Declared.Attributes)
    Magnitude = (
        float(Value)
        if isinstance(Value, (int, float)) and not isinstance(Value, bool)
        else None
    )
    if Magnitude is not None and not IsFinite(Magnitude):
        raise ValueError("Material property values must be finite")
    if Declared.TagName == "Distance" and Magnitude is not None:
        return UnitValue(KMaterialUnits["MilliMeter"], Magnitude)
    if Declared.TagName == "Float" and Magnitude is not None:
        UnitName = Attributes.get("unit")
        if UnitName is None:
            return Magnitude
        if UnitName not in KUnitScales:
            raise ValueError("Fusion material unit has no recorded scale")
        Scale = KUnitScales[UnitName]
        Factor = 10.0 ** abs(Scale)
        return UnitValue(
            KMaterialUnits[UnitName],
            Magnitude * Factor if Scale >= 0 else Magnitude / Factor,
        )
    if Declared.TagName == "Integer" and type(Value) is int:
        return Value
    if Declared.TagName == "Boolean" and type(Value) is bool:
        return Value
    if Declared.TagName == "Color" and isinstance(Value, ColorValue):
        return Value
    if Declared.TagName == "Choice" and type(Value) is int:
        Choices = {
            dict(Child.Attributes)["val"]
            for Child in Declared.Children
            if Child.TagName == "ChoiceValue"
        }
        if str(Value) not in Choices:
            raise ValueError("Material choice is not declared by its Fusion schema")
        return Value
    raise ValueError("Material property type differs from its Fusion schema")
