from convert.formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.formats.Fusion.SegmentCodec.Features.Schema.ClassLayout import ClassLayout
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldSpec import FieldSpec

KExtrudeLayout = ClassLayout(
    ClassStamp(
        "DD405BC2-D673-44F0-8833-5CB2A1C186C7",
        "3FED63D9-CDC5-4334-A5C5-6C10271320D5",
        8,
    ),
    (
        FieldSpec("ProfileFromEntityRef", FieldKind.KStrongRef),
        FieldSpec("bIsAGDExtrudeFeature", FieldKind.KBoolean),
        FieldSpec("bPreviewNormal", FieldKind.KBoolean),
        FieldSpec("booleanOperation", FieldKind.KUnsigned),
        FieldSpec("directionType", FieldKind.KUnsigned),
        FieldSpec("extendFaceOption", FieldKind.KUnsigned),
        FieldSpec("isFlipDirection", FieldKind.KBoolean),
        FieldSpec("isSolidOperation", FieldKind.KBoolean),
        FieldSpec("profileLocaltionType", FieldKind.KUnsigned),
        FieldSpec("profileNormal", FieldKind.KVector),
        FieldSpec("profileOffset", FieldKind.KStrongRef),
        FieldSpec("rAgainstDistance", FieldKind.KStrongRef),
        FieldSpec("rAlongDistance", FieldKind.KStrongRef),
        FieldSpec("rExtrudeToolBody", FieldKind.KStrongRef),
        FieldSpec("rFromEntityRef", FieldKind.KStrongRef),
        FieldSpec("rTaperAngle", FieldKind.KStrongRef),
        FieldSpec("rToEntityRef", FieldKind.KStrongRef),
        FieldSpec("side1ExtentType", FieldKind.KUnsigned),
        FieldSpec("side1Offset", FieldKind.KStrongRef),
        FieldSpec("side1SolutionType", FieldKind.KUnsigned),
        FieldSpec("side2ExtendFaceOption", FieldKind.KUnsigned),
        FieldSpec("side2ExtentType", FieldKind.KUnsigned),
        FieldSpec("side2FlipDirection", FieldKind.KBoolean),
        FieldSpec("side2Offset", FieldKind.KStrongRef),
        FieldSpec("side2SolutionType", FieldKind.KUnsigned),
        FieldSpec("side2TaperAngle", FieldKind.KStrongRef),
        FieldSpec("startDirectionFlip", FieldKind.KBoolean),
        FieldSpec("symmetricMeasurementType", FieldKind.KUnsigned),
        FieldSpec("thinExtrude", FieldKind.KBoolean),
        FieldSpec("thinExtrudeSide1WallLocation", FieldKind.KUnsigned),
        FieldSpec("thinExtrudeSide1WallThickness", FieldKind.KStrongRef),
        FieldSpec("thinExtrudeSide2WallLocation", FieldKind.KUnsigned),
        FieldSpec("thinExtrudeSide2WallThickness", FieldKind.KStrongRef),
    ),
)
