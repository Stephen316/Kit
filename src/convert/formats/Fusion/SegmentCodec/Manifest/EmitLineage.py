from typing import cast as CastValue

from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLayout import KExportLabel
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestSink import ManifestSink


# the lineage operation needs a consistent construction rule so native records retain their segment ownership and schema
def EmitLineage(SinkValue: ManifestSink, Lineage: tuple[str, str] | None) -> None:
    if Lineage is None:
        SinkValue.AddBytes(b"\1")
        SinkValue.AddText(KExportLabel, WideText=True)
    elif type(Lineage) is tuple and len(CastValue(tuple[object, ...], Lineage)) == 2:
        SinkValue.AddBytes(b"\0")
        SinkValue.AddText(Lineage[0], WideText=True)
        SinkValue.AddText(Lineage[1], WideText=True)
    else:
        raise ValueError("Invalid Fusion root manifest lineage")
