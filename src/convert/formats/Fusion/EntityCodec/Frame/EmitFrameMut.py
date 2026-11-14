from convert.formats.Fusion.EntityCodec.Frame.EmitNamedMut import EmitNamedMut
from convert.formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Schema.CheckReference import CheckReference
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.EmitAtom import EmitAtom
from convert.formats.Fusion.EntityCodec.Wire.EmitReference import EmitReference
from convert.formats.Fusion.SegmentCodec.Features.Binary.EmitText import EmitText
from convert.formats.Fusion.SegmentCodec.Features.Binary.FeatureSink import FeatureSink


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
