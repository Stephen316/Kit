from functools import cache as MakeCache

from convert.formats.Fusion.DrawingCodec.Dwg.Objects.RecordSpecs import KRecordSpecs
from convert.formats.Fusion.DrawingCodec.Dwg.Records.ParseSpec import ParseSpec
from convert.formats.Fusion.DrawingCodec.Dwg.Records.SpecOp import SpecOp


@MakeCache
def LookupSpec(SpecKey: str) -> tuple[SpecOp, ...]:
    SpecText = KRecordSpecs.get(SpecKey)
    if SpecText is None:
        raise ValueError(f"DWG record spec {SpecKey!r} is unknown")
    return ParseSpec(SpecText)
