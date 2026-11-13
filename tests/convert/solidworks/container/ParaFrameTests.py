from io import BytesIO
from pathlib import Path as FilePath
from pytest import mark as TestMark, raises as RaisesError
from convert.adapters.solidworks.core.Adapter import ReadSldprt, WriteSldprt
from convert.adapters.solidworks.container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.container.Parasolid import DecodePartition
from convert.adapters.solidworks.container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.container.Format import (
    PARTITION_STREAM as PartitionStream,
)
from tests.convert.solidworks.container.FrameFixture import FrameFixture

KSample = (
    FilePath(__file__).parents[4]
    / "re"
    / "solidworks"
    / "examples"
    / ".SLDPRT"
    / "example.SLDPRT"
)


@TestMark.parametrize("Chained", (True, False))
def TestFrameRead(Chained: bool) -> None:
    Original = ReadSldprt(KSample)
    Streams = SldprtArchive.open(KSample).streams
    Payloads = DecodePartition(Streams[PartitionStream], PartitionStream)
    Sections = [FrameFixture(ItemValue.data, Chained=Chained) for ItemValue in Payloads]
    Streams[PartitionStream] = b"".join(Sections)
    Fixture = BuildSldprt(Streams, template=KSample.read_bytes())
    Document = ReadSldprt(Fixture)
    assert [
        (ItemValue.data, ItemValue.sha256) for ItemValue in Document.brep_payloads
    ] == [(ItemValue.data, ItemValue.sha256) for ItemValue in Original.brep_payloads]
    assert Document.brep == Original.brep
    assert Document.feature_timeline == Original.feature_timeline
    Extracted = [
        ItemValue
        for ItemValue in Document.brep_payloads
        if ItemValue.source_stream == PartitionStream
    ]
    for ItemValue, Section in zip(Extracted, Sections, strict=True):
        assert ItemValue.provenance is not None
        assert ItemValue.provenance.spans[0].length == len(Section)
    Output = BytesIO()
    _ = WriteSldprt(Document, Output)
    assert Output.getvalue() == Fixture


@TestMark.parametrize("Damage", ("checksum", "truncated", "trailing", "size"))
def TestFrameDamage(Damage: str) -> None:
    Streams = SldprtArchive.open(KSample).streams
    Payloads = DecodePartition(Streams[PartitionStream], PartitionStream)
    Streams[PartitionStream] = b"".join(
        FrameFixture(ItemValue.data, Damage=Damage if Index == 0 else "")
        for Index, ItemValue in enumerate(Payloads)
    )
    Fixture = BuildSldprt(Streams, template=KSample.read_bytes())
    with RaisesError(SldprtFormat):
        _ = ReadSldprt(Fixture)
    Document = ReadSldprt(Fixture, strict=False)
    assert any(
        ItemValue.code == "sldprt.parasolid_decode_failed"
        for ItemValue in Document.diagnostics
    )
    assert all(
        ItemValue.source_stream != PartitionStream
        for ItemValue in Document.brep_payloads
    )
