from convert.formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.EmitAtom import EmitAtom


def EmitMatrix(Value: KEntityValue, Shape: WireType) -> bytes:
    if not isinstance(Value, MatrixValue):
        raise ValueError("Fusion entity matrix requires a typed matrix value")
    if Value.Entries is None:
        return b"\1"
    if not Shape.HasMatrixRows or len(Value.Entries) != 16:
        raise ValueError("Fusion entity profile does not qualify these matrix rows")
    return b"\0" + b"".join(EmitAtom(Entry, WireType("f64")) for Entry in Value.Entries)
