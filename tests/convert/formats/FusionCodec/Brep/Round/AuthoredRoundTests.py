from pathlib import Path as FilePath

from pytest import approx as ApproxValue, mark as TestMarks

from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb
from convert.formats.Fusion.BrepCodec.Journal.Round.CreateRoundBody import (
    CreateRoundBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Round.SphereNode import SphereNode
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable
from tests.convert.formats.FusionCodec.Brep.GeometryState.GeometryArchive import (
    GeometryArchive,
)
from tests.convert.formats.FusionCodec.Brep.Journal.JournalArchive import JournalArchive
from tests.convert.formats.FusionCodec.Brep.Round.RoundSamples import (
    KRoundBodies,
    KRoundHistory,
    KRoundStamp,
)


@TestMarks.parametrize("ShapeIndex", (0, 1, 2))
def TestRoundAuthor(TmpPath: FilePath, ShapeIndex: int) -> None:
    Shape = KRoundBodies[ShapeIndex]
    Journal = CreateRoundBody(Shape, KRoundHistory, KRoundStamp)
    Stored = JournalArchive(TmpPath / "RoundHistory.zip", EmitJournal(Journal))
    assert Stored == Journal
    Payload = EmitStateSmb(Stored)
    Parsed = GeometryArchive(TmpPath / "RoundBody.zip", Payload)
    assert Parsed.Entities == Journal.Entities
    Table = ReadAsmTable(Payload)
    assert Table.RootCount == 2
    assert tuple(Value.Name for Value in Table.Records[:5]) == (
        "asmheader",
        "body",
        "lump",
        "shell",
        "face",
    )
    assert len(Table.Records) == 6
    Surface = Parsed.Entities[-1]
    assert isinstance(Surface, (SphereNode, TorusNode))
    assert Surface.CenterCm == ApproxValue(
        tuple(Value / 10 for Value in Shape.CenterMm)
    )
    if isinstance(Surface, SphereNode):
        assert Surface.RadiusCm == ApproxValue(1.9)
    else:
        assert Surface.MajorRadiusCm == ApproxValue(3.1)
        assert Surface.MinorRadiusCm == ApproxValue(0.9)
        assert Surface.AxisVector == ApproxValue(
            (0.0, 0.6, 0.8) if ShapeIndex == 2 else (0.0, 0.0, 1.0)
        )
