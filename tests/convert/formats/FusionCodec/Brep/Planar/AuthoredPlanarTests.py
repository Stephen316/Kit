from collections import Counter
from pathlib import Path as FilePath

from pytest import approx as Approx, mark as TestMarks

from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb
from convert.formats.Fusion.BrepCodec.Journal.Planar.ReadPlanarState import (
    ReadPlanarState,
)
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.CreatePolyBody import (
    CreatePolyBody,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable
from tests.convert.formats.FusionCodec.Brep.Journal.JournalArchive import JournalArchive
from tests.convert.formats.FusionCodec.Brep.Planar.PlanarSamples import (
    KPlanarHistory,
    KPlanarPlace,
    KPlanarStamp,
    MakeTetrahedron,
    MakeTriPrism,
)


@TestMarks.parametrize(
    "ShapeName,Volume,FaceCount",
    (
        ("tetrahedron", 17 * 23 * 31 / 6000, 4),
        ("prism", 19 * 13 * 37 / 2000, 5),
        ("placed", 17 * 23 * 31 / 6000 * 1.25**3, 4),
    ),
)
def TestPolyFile(
    TmpPath: FilePath, ShapeName: str, Volume: float, FaceCount: int
) -> None:
    Shape = MakeTriPrism() if ShapeName == "prism" else MakeTetrahedron()
    Placement = KPlanarPlace if ShapeName == "placed" else None
    Model = CreatePolyBody(Shape, KPlanarHistory, KPlanarStamp, Placement)
    Parsed = JournalArchive(TmpPath / "AuthoredPolyhedron.zip", EmitJournal(Model))
    assert Parsed == Model
    Bodies = ReadPlanarState(Parsed)
    assert len(Bodies) == 1 and Bodies[0].VolumeCm3 == Approx(Volume)
    assert len(Bodies[0].FaceRefs) == FaceCount
    Target = TmpPath / "CurrentPolyhedron.smb"
    _ = Target.write_bytes(EmitStateSmb(Parsed))
    Table = ReadAsmTable(Target.read_bytes())
    Counts = Counter(Record.Name for Record in Table.Records)
    assert Table.RootCount == 2 and Counts["body"] == 1
    assert Counts["face"] == Counts["plane-surface"] == FaceCount
    assert Counts["edge"] == Counts["straight-curve"]
    assert Counts["vertex"] == Counts["point"] == len(Shape.PointsMm)
    assert Counts["ATTRIB_CUSTOM-attrib"] == 0
    assert Counts["transform"] == (1 if Placement is not None else 0)
