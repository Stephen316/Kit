from collections import Counter
from pathlib import Path as FilePath

from pytest import approx as Approx

from convert.formats.Fusion.BrepCodec.Prism.EmitPrismHist import EmitPrismHist
from convert.formats.Fusion.BrepCodec.Prism.ReadPrismHist import ReadPrismHist
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable
from tests.convert.formats.FusionCodec.Brep.Prism.PrismArchive import StorePrism
from tests.convert.formats.FusionCodec.Brep.Prism.PrismSample import MakePrism


def TestPrismHist(TmpPath: FilePath) -> None:
    Sample = MakePrism()
    Payload = EmitPrismHist(
        Sample.Model, Sample.Identity, Sample.TagSet, Sample.History, Sample.Stamp
    )
    Stored = StorePrism(TmpPath / "Prism.zip", Payload)
    Table = ReadAsmTable(Stored)
    Counts = Counter(Entry.Name for Entry in Table.Records)
    assert Table.RootCount == 2 and len(Table.Records) == 102
    assert (Counts["face"], Counts["edge"], Counts["vertex"]) == (6, 12, 8)
    assert Counts["ATTRIB_CUSTOM-attrib"] == 16
    Parsed = ReadPrismHist(Stored)
    assert Parsed.Identity == Sample.Identity
    assert Parsed.TagSet == Sample.TagSet
    assert Parsed.History == Sample.History
    assert Parsed.Model.Width == Approx(17.0)
    assert Parsed.Model.Depth == Approx(23.0)
    assert Parsed.Model.Height == Approx(31.0)
    assert Parsed.Frame.CornersCm[0] == Approx((-0.7, 1.3, 0.5))
    assert Parsed.Frame.CornersCm[7] == Approx((1.0, 3.6, 3.6))
    assert (
        Parsed.Model.Width * Parsed.Model.Depth * Parsed.Model.Height / 1000
    ) == Approx(12.121)
    assert (
        EmitPrismHist(
            Parsed.Model,
            Parsed.Identity,
            Parsed.TagSet,
            Parsed.History,
            Parsed.Stamp,
            Parsed.Frame,
        )
        == Payload
    )
