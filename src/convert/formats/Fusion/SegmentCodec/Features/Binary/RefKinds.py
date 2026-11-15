from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind

# the reference kinds vocabulary must stay centralized so segment reconstruction agrees on supported native identities
KReferenceKinds = frozenset((FieldKind.KStrongRef, FieldKind.KPassiveRef))

# the collection kinds vocabulary must stay centralized so segment reconstruction agrees on supported native identities
KCollectionKinds = frozenset(
    (
        FieldKind.KStrongVector,
        FieldKind.KPassiveVector,
        FieldKind.KPassiveList,
        FieldKind.KStrongSet,
    )
)
