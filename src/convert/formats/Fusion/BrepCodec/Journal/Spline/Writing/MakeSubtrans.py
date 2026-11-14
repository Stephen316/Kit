from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeRefScope import (
    MakeRefScope,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.WideWord import WideWord
from convert.formats.Fusion.BrepCodec.Journal.Spline.Writing.WritePatches import (
    WritePatches,
)
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline


def MakeSubtrans(Value: SubtransNode | SubtypeRef) -> tuple[KAsmToken, ...]:
    if isinstance(Value, SubtypeRef):
        return MakeRefScope(Value, "subtrans")
    return (
        (15, None),
        (13, "t_spl_subtrans_object"),
        WideWord(EmitTspline(Value.Surface).decode("ascii")),
        (10, None),
        WideWord(WritePatches(Value.Regions)),
        (16, None),
    )
