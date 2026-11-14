from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as TestMarks

from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

KRepoRoot = FilePath(__file__).resolve().parents[6]


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize(
    "FileName,HistoryCount,SnapshotCount",
    (
        ("re/Fusion/Study/pipemodes-87cfa7d8d82b/triangular.f3d", 1, 1),
        ("re/Fusion/LocalOracle/PublicAdapter/vendor_circleEdited.f3d", 0, 1),
        ("re/Fusion/LocalOracle/PublicAdapter/vendor_frustumEdited.f3d", 1, 1),
    ),
)
def TestGeneralDoc(
    TmpPath: FilePath, FileName: str, HistoryCount: int, SnapshotCount: int
) -> None:
    Source = KRepoRoot / FileName
    Model = ReadDocument(Source.read_bytes())
    assert len(Model.Bodies) == HistoryCount
    assert len(Model.Snapshots) == SnapshotCount
    assert all(isinstance(Value.Snapshot, GeometryState) for Value in Model.Snapshots)
    Target = TmpPath / "TypedDocument.f3d"
    _ = Target.write_bytes(EmitParsed(Model))
    assert ReadDocument(Target.read_bytes()) == Model
