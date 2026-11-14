from typing import cast as CastValue

from convert.formats.Fusion.ContainerCodec.ContainerLayout import KMaxProperties
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLayout import KPhysicalKey
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestSink import ManifestSink


def EmitPropsMut(SinkValue: ManifestSink, Properties: tuple[tuple[str, str], ...]) -> None:
    SinkValue.AddCount(Properties, KMaxProperties)
    Names: set[str] = set()
    for Entry in Properties:
        if (
            type(Entry) is not tuple
            or len(CastValue(tuple[object, ...], Entry)) != 2
            or type(Entry[0]) is not str
            or not Entry[0]
            or Entry[0] in Names
        ):
            raise ValueError("Invalid Fusion asset property")
        Names.add(Entry[0])
        SinkValue.AddText(Entry[0])
        if Entry[0] == KPhysicalKey:
            SinkValue.AddGuid(Entry[1])
        else:
            SinkValue.AddText(Entry[1], WideText=True)
