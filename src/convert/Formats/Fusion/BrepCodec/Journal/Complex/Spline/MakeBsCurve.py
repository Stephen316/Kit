from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsCurve import (
    CheckBsCurve,
)
from convert.Formats.Fusion.BrepCodec.Journal.Complex.Spline.MakeKnots import (
    MakeKnots,
    MakePoles,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    EnumWord,
    IntWord,
    NameWord,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


# the bs curve operation needs a consistent construction rule so nested spline and surface records retain their relationships
def MakeBsCurve(Value: BsCurve, Dimension: int) -> tuple[KAsmToken, ...]:
    CheckBsCurve(Value, Dimension)
    return (
        NameWord("nurbs" if Value.Rational else "nubs"),
        IntWord(Value.Degree),
        EnumWord(Value.Closure),
        IntWord(len(Value.Knots)),
        *MakeKnots(Value.Knots, Value.Multiplicity),
        *MakePoles(Value.Poles, Value.Weights),
    )


# the bs option operation needs a consistent construction rule so nested spline and surface records retain their relationships
def MakeBsOption(Value: BsCurve | None) -> tuple[KAsmToken, ...]:
    return (NameWord("nullbs"),) if Value is None else MakeBsCurve(Value, 2)
