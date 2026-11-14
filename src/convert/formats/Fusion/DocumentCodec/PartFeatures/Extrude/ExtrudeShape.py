from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.AddParamMut import (
    AddParamMut,
    ExprText,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)

KBooleanCodes = {"join": 1, "cut": 2, "intersect": 3, "new": 4}
KDirectionCodes = {"two": 2, "symmetric": 3}
KZeroAngle = "0.0 deg"


def ExtrudeShape(Feature: ExtrudeSpec) -> dict[str, object]:
    IsTwoSided = Feature.Extent in ("two", "symmetric")
    return dict(
        booleanOperation=KBooleanCodes[Feature.Operation],
        directionType=KDirectionCodes.get(Feature.Extent, 1),
        extendFaceOption=1 if IsTwoSided else 2,
        side2ExtentType=1 if Feature.Extent == "two" else 0,
        side2ExtendFaceOption=1 if IsTwoSided else 0,
        symmetricMeasurementType=1 if Feature.Extent == "symmetric" else 0,
    )


def AddExtentParams(
    Author: AuthorState, Prefix: str, Feature: ExtrudeSpec
) -> list[str]:
    Reference = Author.Reference
    MainRole = Prefix + "feature"
    IsFlip = Feature.Extent == "flip"
    Along = -Feature.DistanceMm if IsFlip else Feature.DistanceMm
    Written = "-( " + ExprText(Feature.DistanceMm) + " mm )" if IsFlip else None
    AddParamMut(
        Author, Prefix + "along", MainRole, "AlongDistance", Along, "mm", Written
    )
    AddParamMut(
        Author, Prefix + "taper", MainRole, "TaperAngle", 0.0, "deg", KZeroAngle
    )
    Roles = [Prefix + "along", Prefix + "taper"]
    Fields: dict[str, object] = dict(
        rAlongDistance=Reference(Prefix + "along"),
        rTaperAngle=Reference(Prefix + "taper"),
    )
    if Feature.Extent == "symmetric":
        Fields["side2TaperAngle"] = Reference(Prefix + "taper")
    if Feature.Extent == "two":
        AddParamMut(
            Author,
            Prefix + "against",
            MainRole,
            "AgainstDistance",
            Feature.AgainstMm,
            "mm",
        )
        AddParamMut(
            Author,
            Prefix + "side_taper",
            MainRole,
            "Side2TaperAngle",
            0.0,
            "deg",
            KZeroAngle,
        )
        Roles.extend([Prefix + "against", Prefix + "side_taper"])
        Fields["rAgainstDistance"] = Reference(Prefix + "against")
        Fields["side2TaperAngle"] = Reference(Prefix + "side_taper")
    Author.Change(MainRole, **Fields, **ExtrudeShape(Feature))
    return Roles
