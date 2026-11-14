from convert.formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldSpec import FieldSpec

KCoreLayout = ClassLayout(
    ClassStamp(
        "A2052F46-21B4-4AAA-9AF1-C371F0AB6CAB",
        "E8BDB9D4-2E39-405C-B05E-E2206AD3F125",
        4,
    ),
    (
        FieldSpec("associationId", FieldKind.KUuidText),
        FieldSpec("bDisabled", FieldKind.KBoolean),
        FieldSpec("bLockedForTimelineReorder", FieldKind.KBoolean),
        FieldSpec("bLockedForTimelineRoll", FieldKind.KBoolean),
        FieldSpec("childNodes", FieldKind.KPassiveList),
        FieldSpec("endCacheHS", FieldKind.KInteger, 0x32),
        FieldSpec("endModelHS", FieldKind.KInteger),
        FieldSpec("featureBaseName", FieldKind.KUnicode),
        FieldSpec("featureIndex", FieldKind.KIdentity),
        FieldSpec("featureUserName", FieldKind.KUnicode),
        FieldSpec("groupMembers", FieldKind.KPassiveList),
        FieldSpec("isImplicitlySuppressed", FieldKind.KBoolean),
        FieldSpec("isSuppressed", FieldKind.KBoolean),
        FieldSpec("isZombieFeature", FieldKind.KBoolean),
        FieldSpec("rProgenitorTable", FieldKind.KStrongRef),
        FieldSpec("rReferencedContext", FieldKind.KPassiveRef),
        FieldSpec("startCacheHS", FieldKind.KInteger, 0x32),
        FieldSpec("startModelHS", FieldKind.KInteger),
    ),
)
