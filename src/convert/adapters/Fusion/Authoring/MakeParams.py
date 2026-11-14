from math import radians as ToRadians

from convert.adapters.Fusion.Authoring.ProfileShape import HasSolid
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.enums.EnumValues import ValueKind
from interchange.records.RecordParameter import Expression, Parameter, ParameterValue


def MakeLength(
    Identity: str,
    NameValue: str,
    Amount: float,
    Owner: str = "",
    ExpressionText: str | None = None,
    Dependency: str | None = None,
    Comment: str = "",
) -> Parameter:
    ExpressionValue = (
        None
        if ExpressionText is None
        else Expression(ExpressionText, () if Dependency is None else (Dependency,))
    )
    return Parameter(
        Identity,
        NameValue,
        ParameterValue(Amount, ValueKind.KLength, "mm"),
        expression=ExpressionValue,
        owner_id=Owner,
        attributes={"comment": Comment},
    )


def MakeParams(SpecValue: DocumentSpec) -> tuple[Parameter, ...]:
    Values = [
        MakeLength(
            "length",
            SpecValue.ParamName,
            SpecValue.LengthMm,
            Comment=SpecValue.ParamComment,
        )
    ]
    if SpecValue.ConstrainRectangle:
        Values.extend(
            (
                MakeLength("width", SpecValue.WidthParamName, SpecValue.WidthMm),
                MakeLength("depth", SpecValue.DepthParamName, SpecValue.DepthMm),
            )
        )
        Values.extend(
            (
                MakeLength(
                    "width-dimension",
                    "Width",
                    SpecValue.WidthMm,
                    "sketch",
                    SpecValue.WidthParamName,
                    "width",
                ),
                MakeLength(
                    "depth-dimension",
                    "Depth",
                    SpecValue.DepthMm,
                    "sketch",
                    SpecValue.DepthParamName,
                    "depth",
                ),
            )
        )
    if HasSolid(SpecValue):
        Values.append(
            MakeLength(
                "along",
                "AlongDistance",
                SpecValue.LengthMm,
                "extrude",
                SpecValue.ParamName,
                "length",
            )
        )
        Values.append(
            Parameter(
                "taper",
                "TaperAngle",
                ParameterValue(
                    ToRadians(SpecValue.TaperDegrees), ValueKind.KAngle, "rad"
                ),
                owner_id="extrude",
            )
        )
    return tuple(Values)
