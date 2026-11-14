from dataclasses import replace as Replace
from struct import pack as PackValue

from pytest import mark as TestMark, raises as Raises

from convert.formats.Fusion.ContainerCodec.Model.DocProps import DocProps
from convert.formats.Fusion.ContainerCodec.Model.DocRedirects import DocRedirects
from convert.formats.Fusion.ContainerCodec.Model.DocStruct import DocStruct
from convert.formats.Fusion.ContainerCodec.Model.RedirectDesign import (
    RedirectDesign,
)
from convert.formats.Fusion.ContainerCodec.Model.RedirectRef import RedirectRef
from convert.formats.Fusion.ContainerCodec.Wire.EmitDocProps import EmitDocProps
from convert.formats.Fusion.ContainerCodec.Wire.EmitRedirects import EmitRedirects
from convert.formats.Fusion.ContainerCodec.Wire.ReadDocProps import ReadDocProps
from convert.formats.Fusion.ContainerCodec.Wire.ReadRedirects import ReadRedirects
from convert.formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.formats.Fusion.EntityCodec.Wire.EmitReference import EmitCrossRef
from convert.formats.Fusion.EntityCodec.Wire.ReadRefMut import ReadRefMut
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Manifest.EmitRootWire import EmitRootWire
from convert.formats.Fusion.SegmentCodec.Manifest.LinkLayout import (
    KLinkedAsset,
    KLinkedUrl,
)
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLink import ManifestLink
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestTypes import RootManifest
from convert.formats.Fusion.SegmentCodec.Manifest.ReadRootWire import ReadRootWire
from convert.formats.Fusion.SegmentCodec.Metadata.EmitMetaCtx import EmitMetaCtx
from convert.formats.Fusion.SegmentCodec.Metadata.MetaContext import MetaContext
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaCtx import ReadMetaCtx
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadRootMeta import (
    KRootKeys,
)

KVersionUrn = "urn:adsk.wipprod:fs.file:vf.SyntheticLineageKey000?version=3"

KLineageUrn = "urn:adsk.wipprod:dm.lineage:SyntheticLineageKey000"

KTypeGuid = "D956D02C-2806-4E57-8B2E-EFA323A5C2B8"

KSyntheticLink = ManifestLink(
    "7a123456-1111-4222-8333-abcdef123456",
    "/synthetic/source/Root.f3d",
    "/synthetic/cache/_Part.7b123456-1111-4222-8333-abcdef123456.f3d",
    "/synthetic/xref/Part.f3d",
    (
        ("LineageId", KLineageUrn),
        ("toDocDisplayName", "Synthetic Part"),
        (KLinkedUrl, KVersionUrn),
        (KLinkedAsset, "7c123456-1111-4222-8333-abcdef123456"),
    ),
)

KSyntheticRoot = RootManifest(
    "Linked Root",
    "",
    (
        "6a123456-1111-4222-8333-abcdef123456",
        "6b123456-1111-4222-8333-abcdef123456",
    ),
    (1, 2),
    tuple((KeyName, Index + 70) for Index, KeyName in enumerate(KRootKeys)),
    "6c123456-1111-4222-8333-abcdef123456",
    ("6d123456-1111-4222-8333-abcdef123456",),
    (KSyntheticLink,),
    ("Linked Root", KLineageUrn),
)

KSyntheticContext = MetaContext(
    (1 << 63) + 17,
    KSyntheticLink.LinkId,
    "7d123456-1111-4222-8333-abcdef123456",
    KVersionUrn,
    "7c123456-1111-4222-8333-abcdef123456",
    1,
)

KSyntheticRedirects = DocRedirects(
    (
        RedirectDesign(
            4, "Root.f3d", "Linked Root", KLineageUrn, KVersionUrn.replace("3", "4")
        ),
        RedirectDesign(3, "Part.f3d", "Synthetic Part", KLineageUrn, KVersionUrn),
    ),
    (
        RedirectRef(
            "Root.f3d",
            "Part.f3d",
            (("neutronRole", KSyntheticLink.LinkId), ("neutronData", "")),
        ),
    ),
)


def EmitContexts(Items: tuple[MetaContext, ...]) -> bytes:
    SinkValue = MetaSink()
    EmitMetaCtx(SinkValue, Items)
    return bytes(SinkValue.Buffer)


def TestRootLinks() -> None:
    Payload = EmitRootWire(KSyntheticRoot)
    assert ReadRootWire(Payload) == KSyntheticRoot
    Plain = Replace(KSyntheticRoot, Ancestry=(), Links=(), Lineage=None)
    assert ReadRootWire(EmitRootWire(Plain)) == Plain


@TestMark.parametrize(
    "Value",
    (
        Replace(KSyntheticRoot, Links=(KSyntheticLink, KSyntheticLink)),
        Replace(
            KSyntheticRoot,
            Links=(
                Replace(
                    KSyntheticLink,
                    Properties=KSyntheticLink.Properties[:1] * 2,
                ),
            ),
        ),
    ),
)
def TestBadLinks(Value: RootManifest) -> None:
    with Raises(ValueError):
        _ = EmitRootWire(Value)


def TestLinkWords() -> None:
    Payload = EmitRootWire(KSyntheticRoot)
    Words = PackValue("<4I", 2, 4, 1, 0)
    assert Payload.count(Words) == 1
    with Raises(ValueError):
        _ = ReadRootWire(Payload.replace(Words, PackValue("<4I", 2, 4, 1, 1)))


def TestContexts() -> None:
    Payload = EmitContexts((KSyntheticContext,))
    assert ReadMetaCtx(MetaCursor(Payload), 1) == (KSyntheticContext,)


@TestMark.parametrize(
    "Value",
    (
        Replace(KSyntheticContext, LinkId=KSyntheticContext.LinkId.upper()),
        Replace(KSyntheticContext, AssetId="00000000-0000-0000-0000-000000000000"),
        Replace(KSyntheticContext, VersionUrn="lineage:SyntheticLineageKey000"),
    ),
)
def TestBadContext(Value: MetaContext) -> None:
    with Raises(ValueError):
        _ = EmitContexts((Value,))


def TestCrossRef() -> None:
    Value = CrossRef(2, (1 << 64) - 3, KTypeGuid)
    Payload = EmitCrossRef(Value)
    Cursor = MetaCursor(Payload)
    assert ReadRefMut(Cursor) == Value
    assert Cursor.Offset == len(Payload) == 60
    with Raises(ValueError):
        _ = ReadRefMut(MetaCursor(Payload[:-1] + b"\1"))


def TestInlineRef() -> None:
    Payload = (
        b"\1"
        + PackValue("<Q", 5)
        + PackValue("<I", 36)
        + KTypeGuid.encode("ascii")
        + b"\0\0"
    )
    assert len(Payload) == 51
    with Raises(ValueError):
        _ = ReadRefMut(MetaCursor(Payload))


def TestDocProps() -> None:
    assert EmitDocProps(None) == bytes(4)
    assert ReadDocProps(bytes(4)) is None
    Value = DocProps(
        DocStruct("1.0.0", "assembly-design", "default", (("hasXrefs", True),))
    )
    Payload = EmitDocProps(Value)
    assert ReadDocProps(Payload) == Value
    assert ReadDocProps(EmitDocProps(DocProps(None))) == DocProps(None)
    with Raises(ValueError):
        _ = ReadDocProps(Payload[:-1])
    with Raises(ValueError):
        _ = ReadDocProps(Payload.replace(b'"version"', b'"Version"'))


def TestRedirects() -> None:
    Payload = EmitRedirects(KSyntheticRedirects)
    assert ReadRedirects(Payload) == KSyntheticRedirects
    Empty = Replace(KSyntheticRedirects, References=())
    assert b'"references":{}' in EmitRedirects(Empty)
    assert ReadRedirects(EmitRedirects(Empty)) == Empty
    with Raises(ValueError):
        _ = ReadRedirects(Payload.replace(b'"type":"XREF"', b'"type":"DERIVED"'))
    with Raises(ValueError):
        _ = EmitRedirects(Replace(KSyntheticRedirects, Designs=()))
