from uuid import UUID as ParseUuid

from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.SegmentCodec.Metadata.MetaContext import MetaContext

# max contexts must remain consistent across callers so native records retain their segment ownership and schema
KMaxContexts = 4096

# max urn text must remain consistent across callers so native records retain their segment ownership and schema
KMaxUrnText = 512


# invalid ctx guid input must fail here so native records retain their segment ownership and schema
def CheckCtxGuid(TextValue: object) -> str:
    if type(TextValue) is not str or len(TextValue) != 36:
        raise ValueError("Invalid Fusion version context GUID")
    try:
        GuidValue = ParseUuid(TextValue)
    except ValueError as ErrorInfo:
        raise ValueError("Invalid Fusion version context GUID") from ErrorInfo
    if GuidValue.int == 0 or str(GuidValue) != TextValue:
        raise ValueError("Invalid Fusion version context GUID")
    return TextValue


# invalid ctx urn input must fail here so native records retain their segment ownership and schema
def CheckCtxUrn(TextValue: object) -> str:
    if (
        type(TextValue) is not str
        or not TextValue.startswith("urn:")
        or not TextValue.isascii()
        or not TextValue.isprintable()
        or len(TextValue) > KMaxUrnText
    ):
        raise ValueError("Invalid Fusion version context URN")
    return TextValue


# the meta ctx operation needs a distinct decoding boundary so native records retain their segment ownership and schema
def ReadMetaCtx(Cursor: MetaCursor, Count: int) -> tuple[MetaContext, ...]:
    if Count > KMaxContexts:
        raise ValueError("Fusion version context count exceeds limit")
    Contexts: list[MetaContext] = []
    for _ in range(Count):
        Token = Cursor.ReadLong()
        LinkId = CheckCtxGuid(Cursor.ReadText(True, Maximum=36))
        RevisionId = CheckCtxGuid(Cursor.ReadText(True, Maximum=36))
        VersionUrn = CheckCtxUrn(Cursor.ReadText(True, Maximum=KMaxUrnText))
        AssetId = CheckCtxGuid(Cursor.ReadText(True, Maximum=36))
        Contexts.append(
            MetaContext(
                Token, LinkId, RevisionId, VersionUrn, AssetId, Cursor.ReadWord()
            )
        )
    return tuple(Contexts)
