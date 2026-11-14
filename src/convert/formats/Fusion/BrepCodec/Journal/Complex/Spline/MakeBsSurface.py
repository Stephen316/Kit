from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsSurface import (
    CheckBsSurface,
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


def MakeBsSurface(Value: BsSurface) -> tuple[KAsmToken, ...]:
    CheckBsSurface(Value)
    return (
        NameWord("nurbs" if Value.Rational else "nubs"),
        IntWord(Value.UDegree),
        IntWord(Value.VDegree),
        *((NameWord(Value.RationalForm),) if Value.Rational else ()),
        EnumWord(Value.UClosure),
        EnumWord(Value.VClosure),
        EnumWord(Value.USingular),
        EnumWord(Value.VSingular),
        IntWord(len(Value.UKnots)),
        IntWord(len(Value.VKnots)),
        *MakeKnots(Value.UKnots, Value.UMultiplicity),
        *MakeKnots(Value.VKnots, Value.VMultiplicity),
        *MakePoles(Value.Poles, Value.Weights),
    )
