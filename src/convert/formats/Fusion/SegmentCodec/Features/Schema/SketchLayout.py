from convert.formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldSpec import FieldSpec

KSketchLayout = ClassLayout(
    ClassStamp(
        "8DA771B7-52ED-42FC-94E2-2353FE141373",
        "A2052F46-21B4-4AAA-9AF1-C371F0AB6CAB",
        5,
    ),
    (
        FieldSpec("bIsAGDDcSketchFeature", FieldKind.KBoolean),
        FieldSpec("dcParameters", FieldKind.KStrongVector),
        FieldSpec("isVisibleBeforeRollback", FieldKind.KBoolean),
        FieldSpec("meshSections", FieldKind.KStrongVector),
        FieldSpec("rLastFeatureBeforeActivate", FieldKind.KPassiveRef, 0x32),
        FieldSpec("rSketch", FieldKind.KStrongRef),
        FieldSpec("rSketchPlaneMatrix", FieldKind.KStrongRef),
        FieldSpec("sketchIsoCurves", FieldKind.KStrongVector),
        FieldSpec("sketchProjects", FieldKind.KStrongVector),
        FieldSpec("sketchSurfaces", FieldKind.KStrongVector),
    ),
)
