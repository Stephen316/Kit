from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsCurve import (
    CheckBsCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.MakeKnots import (
    MakeKnots,
    MakePoles,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.WireWords import (
    EnumWord,
    IntWord,
    NameWord,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


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


def MakeBsOption(Value: BsCurve | None) -> tuple[KAsmToken, ...]:
    return (NameWord("nullbs"),) if Value is None else MakeBsCurve(Value, 2)
