from convert.formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut
from convert.formats.Fusion.MetaCursor import MetaCursor


def ReadMatrixMut(Cursor: MetaCursor, Shape: WireType) -> MatrixValue:
    if ReadAtomMut(Cursor, WireType("bool")):
        return MatrixValue(None)
    if not Shape.HasMatrixRows:
        raise ValueError("Fusion entity profile does not qualify nonidentity matrices")
    return MatrixValue(
        tuple(float(ReadAtomMut(Cursor, WireType("f64"))) for _ in range(16))
    )
