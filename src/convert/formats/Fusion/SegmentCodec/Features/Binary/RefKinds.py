from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind

KReferenceKinds = frozenset((FieldKind.KStrongRef, FieldKind.KPassiveRef))
KCollectionKinds = frozenset(
    (
        FieldKind.KStrongVector,
        FieldKind.KPassiveVector,
        FieldKind.KPassiveList,
        FieldKind.KStrongSet,
    )
)
