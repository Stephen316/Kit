from convert.Formats.Fusion.EntityCodec.Frame.EmitNamedMut import EmitNamedMut
from convert.Formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.Formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.Formats.Fusion.EntityCodec.Schema.CheckReference import CheckReference
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Wire.EmitAtom import EmitAtom
from convert.Formats.Fusion.EntityCodec.Wire.EmitReference import EmitReference
from convert.Formats.Fusion.SegmentCodec.Features.Binary.EmitText import EmitText
from convert.Formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


# the frame operation needs a consistent construction rule so entity identifiers retain their schema and reference meaning
def EmitFrameMut(Frame: EntityFrame, IsPrimary: bool, Catalog: EntityCatalog) -> bytes:
    Output = FeatureSink()
    Output.AddBytes(EmitText(Frame.RootId))
    if not IsPrimary:
        if Frame.Subjects is not None or Frame.Metadata is not None:
            raise ValueError(
                "Fusion entity continuation cannot contain primary framing"
            )
        return bytes(Output.Buffer)
    Output.AddBytes(EmitAtom(Frame.Subjects is not None, WireType("bool")))
    if Frame.Subjects is not None:
        Output.AddCount(Frame.Subjects, KMaxCount)
        for Entry in Frame.Subjects:
            CheckReference(Entry.Target, "", Catalog)
            Output.AddBytes(EmitReference(Entry.Target))
            Output.AddBytes(EmitAtom(Entry.ObserverIndex, WireType("i32")))
    Output.AddBytes(EmitAtom(Frame.Metadata is not None, WireType("bool")))
    if Frame.Metadata is not None:
        Output.AddBytes(EmitNamedMut(Frame.Metadata, Catalog))
    return bytes(Output.Buffer)
