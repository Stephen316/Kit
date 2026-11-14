from convert.formats.Fusion.DocumentCodec.Materials.StoredValue import KInputValue
from convert.formats.Fusion.DocumentCodec.Materials.Vocabulary.MaterialUnits import (
    KMaterialUnits,
    KUnitScales,
)
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import KMaterialValue
from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


def InputValue(Declared: SchemaNode, Value: KMaterialValue) -> KInputValue:
    if isinstance(Value, UnitValue):
        UnitName = (
            "MilliMeter"
            if Declared.TagName == "Distance"
            else dict(Declared.Attributes).get("unit", "")
        )
        if KMaterialUnits.get(UnitName) != Value.UnitCode:
            raise ValueError("Fusion material value unit differs from its schema")
        Scale = KUnitScales[UnitName]
        Factor = 10.0 ** abs(Scale)
        return Value.Magnitude / Factor if Scale >= 0 else Value.Magnitude * Factor
    if isinstance(Value, (bool, int, float, ColorValue)):
        return Value
    raise ValueError("Fusion material value has no semantic input form")
