from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec
from convert.formats.Fusion.MaterialCodec.Models.PropertyValue import KScalarValue
from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue
from convert.formats.Fusion.MaterialCodec.Wire.EncodeBoolean import EncodeBoolean
from convert.formats.Fusion.MaterialCodec.Wire.EncodeFloat import EncodeFloat
from convert.formats.Fusion.MaterialCodec.Wire.EncodeInteger import EncodeInteger
from convert.formats.Fusion.MaterialCodec.Wire.EncodeText import EncodeText


def EncodeScalar(Value: KScalarValue, Field: PropertySpec) -> bytes:
    if Field.ValueKind in ("String", "URL", "Uuid") and isinstance(Value, str):
        return EncodeText(Value)
    if Field.ValueKind in ("Integer", "Choice") and isinstance(Value, int):
        return EncodeInteger(Value)
    if Field.ValueKind == "Boolean" and isinstance(Value, bool):
        return EncodeBoolean(Value)
    if Field.ValueKind == "Float":
        if Field.UnitName is not None and isinstance(Value, UnitValue):
            return EncodeInteger(Value.UnitCode) + EncodeFloat(Value.Magnitude)
        if Field.UnitName is None and isinstance(Value, (int, float)):
            return EncodeFloat(Value)
    if Field.ValueKind == "Color" and isinstance(Value, ColorValue):
        return b"".join(
            EncodeFloat(Channel)
            for Channel in (
                Value.RedValue,
                Value.GreenValue,
                Value.BlueValue,
                Value.AlphaValue,
            )
        )
    if Field.ValueKind == "Reference" and Value is None:
        return b""
    raise ValueError("Fusion material value does not match its declared property type")
