from convert.formats.Fusion.BrepCodec.Prism.Writing.EmitPrismRows import EmitPrismRows
from convert.formats.Fusion.BrepCodec.Wire.CheckBrepRefs import CheckBrepRefs
from convert.formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Validation.CheckSnapshot import (
    CheckSnapshot,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Writing.SnapRecords import (
    SnapRecords,
)
from convert.formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName


def EmitPrismSnap(Value: PrismSnapshot) -> bytes:
    CheckSnapshot(Value)
    Records = SnapRecords(Value)
    CheckBrepRefs(Records, 4)
    return (
        EmitBrepHeader(Value.Stamp, 4, False, 10.0)
        + EmitPrismRows(Records)
        + EncodeSmbName("End-of-ASM-data")
    )
