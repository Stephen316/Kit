from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from zipfile import ZipFile

from pytest import approx as Approx, mark as TestMarks

from convert.formats.Fusion.BrepCodec.EmitHistory import EmitHistory
from convert.formats.Fusion.BrepCodec.EmitSnapshot import EmitSnapshot
from convert.formats.Fusion.BrepCodec.ReadHistory import ReadHistory
from convert.formats.Fusion.BrepCodec.ReadSnapshot import ReadSnapshot
from tests.convert.formats.FusionCodec.Brep.SampleInputs import MakeSample

KRepoRoot = FilePath(__file__).resolve().parents[5]


def TestBrepArchive(TmpPath: FilePath) -> None:
    Sample = MakeSample()
    HistoryBytes = EmitHistory(
        Sample.Model, Sample.Identity, Sample.TagSet, Sample.History, Sample.Stamp
    )
    SnapshotBytes = EmitSnapshot(Sample.Model, Sample.TagSet, Sample.Stamp)
    Target = TmpPath / "BrepArchive.zip"
    with ZipFile(Target, "w") as Archive:
        Archive.writestr("Solved.smbh", HistoryBytes)
        Archive.writestr("Selection.smb", SnapshotBytes)
    with ZipFile(Target) as Archive:
        History = ReadHistory(Archive.read("Solved.smbh"))
        Snapshot = ReadSnapshot(Archive.read("Selection.smb"))
    assert History.Model == Sample.Model
    assert Snapshot.Model == Sample.Model
    assert History.Identity == Sample.Identity
    assert History.History == Sample.History
    assert History.TagSet == Snapshot.TagSet == Sample.TagSet
    assert History.Stamp == Snapshot.Stamp == Sample.Stamp
    assert History.Header.FileVersion == Snapshot.Header.FileVersion == 23200
    assert (History.Header.RootCount, History.Header.Flags, History.Header.Scale) == (
        2,
        3,
        50.0,
    )
    assert (
        Snapshot.Header.RootCount,
        Snapshot.Header.Flags,
        Snapshot.Header.Scale,
    ) == (4, 2, 10.0)
    assert (
        EmitHistory(
            History.Model,
            History.Identity,
            History.TagSet,
            History.History,
            History.Stamp,
        )
        == HistoryBytes
    )
    assert (
        EmitSnapshot(Snapshot.Model, Snapshot.TagSet, Snapshot.Stamp) == SnapshotBytes
    )


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestNativeBrep(TmpPath: FilePath) -> None:
    Source = KRepoRoot / "re/Fusion/LocalOracle/Features/extrude_07mm.f3d"
    with ZipFile(Source) as Archive:
        Names = tuple(
            NameValue for NameValue in Archive.namelist() if NameValue.endswith(".smbh")
        )
        assert len(Names) == 1
        Value = ReadHistory(Archive.read(Names[0]))
    assert Value.Model.Radius == Approx(10.0)
    assert Value.Model.Height == Approx(7.0)
    assert Value.Model.BasePoint == Approx((0, 0, 0))
    assert Value.Identity.BodyKey == 0
    assert Value.Identity.OperationId == 301
    assert Value.Identity.SecondaryId == 4
    assert Value.History.CurrentId == Value.History.CurrentStateId == 4
    assert Value.History.InitialId == 2
    assert Value.Stamp.Product == "Autodesk Neutron"
    assert Value.TagSet.Sketch.PrimaryId == 102
    assert Value.Vertices.TopIndex == 2
    assert Value.Vertices.BottomIndex == 0
    Target = TmpPath / "Reconstructed.smbh"
    _ = Target.write_bytes(
        EmitHistory(
            Value.Model,
            Value.Identity,
            Value.TagSet,
            Value.History,
            Value.Stamp,
            Value.Vertices,
        )
    )
    assert ReadHistory(Target.read_bytes()) == Value
