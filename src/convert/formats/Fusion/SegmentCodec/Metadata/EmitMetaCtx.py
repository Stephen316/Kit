from typing import cast as CastValue

from convert.formats.Fusion.SegmentCodec.Metadata.MetaContext import MetaContext
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaCtx import (
    CheckCtxGuid,
    CheckCtxUrn,
    KMaxContexts,
)


def EmitMetaCtx(SinkValue: MetaSink, Items: tuple[MetaContext, ...]) -> None:
    if type(Items) is not tuple or len(Items) > KMaxContexts:
        raise ValueError("Invalid Fusion version context sequence")
    for Entry in Items:
        if not isinstance(CastValue(object, Entry), MetaContext):
            raise ValueError("Invalid Fusion version context row")
        SinkValue.AddLong(Entry.Token)
        SinkValue.AddText(CheckCtxGuid(Entry.LinkId), WideText=True)
        SinkValue.AddText(CheckCtxGuid(Entry.RevisionId), WideText=True)
        SinkValue.AddText(CheckCtxUrn(Entry.VersionUrn), WideText=True)
        SinkValue.AddText(CheckCtxGuid(Entry.AssetId), WideText=True)
        SinkValue.AddWord(Entry.SegmentId)
