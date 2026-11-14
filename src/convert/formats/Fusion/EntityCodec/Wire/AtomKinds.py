from convert.formats.Fusion.EntityCodec.Schema.WireType import KWireKind
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind

KAtomKinds: dict[KWireKind, tuple[str, int, int, int]] = {
    "bool": ("B", 1, 0, 1), "u8": ("B", 1, 0, 255), "u16": ("H", 2, 0, 65535),
    "u32": ("I", 4, 0, (1 << 32) - 1), "u64": ("Q", 8, 0, (1 << 64) - 1),
    "i32": ("i", 4, -(1 << 31), (1 << 31) - 1), "f32": ("f", 4, 0, 0), "f64": ("d", 8, 0, 0)
}
KSharedKinds: dict[KWireKind, FieldKind] = {
    "bool": FieldKind.KBoolean, "u32": FieldKind.KUnsigned, "u64": FieldKind.KIdentity,
    "i32": FieldKind.KInteger, "f64": FieldKind.KDecimal
}
