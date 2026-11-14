from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeBound import MakeBound
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeJumps import MakeJumps
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeNubsSurf import (
    MakeNubsSurf,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeSubtrans import (
    MakeSubtrans,
)


def MakeTsplSurf(Value: TsplineSurf) -> tuple[KAsmToken, ...]:
    return (
        (15, None),
        (13, "t_spl_sur"),
        (4, Value.Revision),
        (21, 0),
        *MakeNubsSurf(Value.Cache),
        (6, Value.FitTolerance),
        *MakeJumps(Value.Jumps),
        (11, None),
        *(Field for Bound in Value.Ranges for Field in MakeBound(Bound)),
        (21, Value.TypeCode),
        *MakeSubtrans(Value.Subtrans),
        (4, Value.FaceIndex),
        (16, None),
    )
