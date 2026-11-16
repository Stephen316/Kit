from pathlib import Path as FilePath

from pytest import approx as Approx

from convert.Formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlanarState import (
    ReadPlanarState,
)
from convert.Formats.Fusion.BrepCodec.Journal.PolyAuthor.CreatePolyBody import (
    CreatePolyBody,
)
from tests.Convert.Formats.FusionCodec.Brep.Journal.JournalArchive import JournalArchive
from tests.Convert.Formats.FusionCodec.Brep.Planar.PlanarSamples import (
    KPlanarHistory,
    KPlanarPlace,
    KPlanarStamp,
    MakeTetrahedron,
)


# the placed poly contract needs boundary coverage so stored document relationships remain consistent
def TestPlacedPoly(TmpPath: FilePath) -> None:
    Model = CreatePolyBody(
        MakeTetrahedron(), KPlanarHistory, KPlanarStamp, KPlanarPlace
    )
    Parsed = JournalArchive(TmpPath / "PlacedPolyhedron.zip", EmitJournal(Model))
    Shape = ReadPlanarState(Parsed)[0]
    assert Shape.Placement == KPlanarPlace
    assert Shape.PointsCm[0] == Approx((1.1, -0.7, 0.5))
    assert Shape.PointsCm[1] == Approx((1.1, 1.425, 0.5))
    assert Shape.PointsCm[2] == Approx((-1.775, -0.7, 0.5))
    assert Shape.PointsCm[3] == Approx((1.1, -0.7, 4.375))
    assert Shape.VolumeCm3 == Approx(3.945638020833333)
