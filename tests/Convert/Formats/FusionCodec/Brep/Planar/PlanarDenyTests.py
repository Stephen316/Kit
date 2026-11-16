from pathlib import Path as FilePath

from pytest import mark as TestMarks, raises as RaisesError

from convert.Formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.Formats.Fusion.BrepCodec.Journal.EmitStateSmb import EmitStateSmb
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlanarState import (
    ReadPlanarState,
)
from convert.Formats.Fusion.BrepCodec.Journal.PolyAuthor.CreatePolyBody import (
    CreatePolyBody,
)
from tests.Convert.Formats.FusionCodec.Brep.Journal.JournalArchive import JournalArchive
from tests.Convert.Formats.FusionCodec.Brep.Planar.AlterPlanar import AlterPlanar
from tests.Convert.Formats.FusionCodec.Brep.Planar.PlanarSamples import (
    KPlanarHistory,
    KPlanarPlace,
    KPlanarStamp,
    MakeTetrahedron,
)


# the planar deny contract needs boundary coverage so stored document relationships remain consistent
@TestMarks.parametrize(
    "Fault", ("face-winding", "curve-origin", "zero-direction", "singular-transform")
)
def TestPlanarDeny(TmpPath: FilePath, Fault: str) -> None:
    Model = CreatePolyBody(
        MakeTetrahedron(), KPlanarHistory, KPlanarStamp, KPlanarPlace
    )
    Changed = AlterPlanar(Model, Fault)
    Parsed = JournalArchive(TmpPath / "InvalidPlanarShape.zip", EmitJournal(Changed))
    with RaisesError(ValueError):
        _ = ReadPlanarState(Parsed)


# the empty state contract needs boundary coverage so stored document relationships remain consistent
def TestEmptyState(TmpPath: FilePath) -> None:
    Model = CreatePolyBody(MakeTetrahedron(), KPlanarHistory, KPlanarStamp)
    Parsed = JournalArchive(TmpPath / "EmptyInitialState.zip", EmitJournal(Model))
    assert ReadPlanarState(Parsed, 2) == ()
    with RaisesError(ValueError, match="live body"):
        _ = EmitStateSmb(Parsed, 2)
