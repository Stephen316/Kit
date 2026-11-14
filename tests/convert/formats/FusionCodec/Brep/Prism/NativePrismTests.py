from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import approx as Approx, mark as TestMarks

from convert.formats.Fusion.BrepCodec.Prism.EmitPrismHist import EmitPrismHist
from convert.formats.Fusion.BrepCodec.Prism.ReadPrismHist import ReadPrismHist
from tests.convert.formats.FusionCodec.Brep.Prism.PrismArchive import (
    ReadPrismFile,
    StorePrism,
)

KRepoRoot = FilePath(__file__).resolve().parents[6]
KNativeSource = (
    KRepoRoot
    / "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d"
)


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestNativePrism(TmpPath: FilePath) -> None:
    Value = ReadPrismHist(ReadPrismFile(KNativeSource))
    assert (Value.Model.Width, Value.Model.Depth, Value.Model.Height) == Approx(
        (40.0, 30.0, 25.0)
    )
    assert Value.Model.BasePoint == Approx((0.0, 0.0, 0.0))
    assert (Value.Identity.BodyKey, Value.Identity.OperationId) == (0, 301)
    assert Value.Identity.SecondaryId == 7
    assert (Value.History.CurrentId, Value.History.InitialId) == (4, 2)
    assert tuple(Entry.PrimaryId for Entry in Value.TagSet.Faces) == (
        "1",
        "2",
        "4",
        "6",
        "3",
        "5",
    )
    assert tuple(Entry.PrimaryId for Entry in Value.TagSet.Sketches) == (
        105,
        106,
        107,
        108,
    )
    assert Value.Frame.FaceReverse[0]
    assert sum(Entry.Curve.LowerBound is not None for Entry in Value.Frame.Edges) == 4
    assert (
        sum(
            Index == Value.Frame.Edges[Owner].EndCorner
            for Index, Owner in enumerate(Value.Frame.VertexOwners)
        )
        == 7
    )
    Payload = EmitPrismHist(
        Value.Model,
        Value.Identity,
        Value.TagSet,
        Value.History,
        Value.Stamp,
        Value.Frame,
    )
    assert ReadPrismHist(StorePrism(TmpPath / "Canonical.zip", Payload)) == Value
