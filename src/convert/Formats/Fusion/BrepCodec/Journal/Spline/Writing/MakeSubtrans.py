from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Writing.MakeRefScope import (
    MakeRefScope,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Writing.WideWord import WideWord
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Writing.WritePatches import (
    WritePatches,
)
from convert.Formats.Fusion.TSplineCodec.EmitTspline import EmitTspline


# the subtrans operation needs a consistent construction rule so topology changes retain their native revision relationships
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
