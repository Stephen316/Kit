from math import radians as ToRadians
from re import fullmatch as FullMatch

from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import NumberValue, TextValue
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from interchange.records.RecordParameter import Expression


def ParamExpression(
    NodeValue: NativeNode, Catalog: dict[str, NativeNode]
) -> Expression:
    Source = TextValue(NodeValue.Fields["expression"])
    Target = Catalog.get(Source)
    if Target is not None:
        if (
            Target.Fields["isUserDefined"] is not True
            or Target == NodeValue
            or Target.Fields["unit"] != NodeValue.Fields["unit"]
            or TextValue(Target.Fields["expression"]) in Catalog
        ):
            raise ValueError("Unsupported native parameter expression dependency")
        SameNumbers(
            (NumberValue(Target.Fields["value"]),),
            (NumberValue(NodeValue.Fields["value"]),),
        )
        return Expression(Source, (Target.Identity,), "fusion")
    Match = FullMatch(
        r"\s*([+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)\s*(mm|cm|m|in|ft|deg|rad)?\s*",
        Source,
    )
    if Match is None:
        raise ValueError(
            "Native parameter formula is outside the qualified literal/reference grammar"
        )
    UnitName = Match.group(2) or TextValue(NodeValue.Fields["unit"])
    Amount = float(Match.group(1))
    if NodeValue.Fields["unit"] == "deg":
        if UnitName not in ("deg", "rad"):
            raise ValueError(
                "Native angular parameter expression has incompatible units"
            )
        Amount = ToRadians(Amount) if UnitName == "deg" else Amount
    else:
        Factors = {"mm": 0.1, "cm": 1.0, "m": 100.0, "in": 2.54, "ft": 30.48}
        if UnitName not in Factors:
            raise ValueError(
                "Native length parameter expression has incompatible units"
            )
        Amount *= Factors[UnitName]
    SameNumbers((Amount,), (NumberValue(NodeValue.Fields["value"]),))
    return Expression(Source, language="fusion")
