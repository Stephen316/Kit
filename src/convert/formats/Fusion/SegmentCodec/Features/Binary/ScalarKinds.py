from types import MappingProxyType as ReadOnlyMap

from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind

KScalarKinds = ReadOnlyMap(
    {
        FieldKind.KBoolean: ("B", 1, 0, 1),
        FieldKind.KUnsigned: ("I", 4, 0, (1 << 32) - 1),
        FieldKind.KInteger: ("i", 4, -(1 << 31), (1 << 31) - 1),
        FieldKind.KIdentity: ("Q", 8, 0, (1 << 64) - 1),
        FieldKind.KDecimal: ("d", 8, 0, 0),
    }
)
