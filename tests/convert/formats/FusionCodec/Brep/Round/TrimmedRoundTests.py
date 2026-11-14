from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as TestMarks

from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.PermuteJournal import PermuteJournal
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.Journal.Round.SphereNode import SphereNode
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from tests.convert.formats.FusionCodec.Brep.Frustum.NativeHistory import NativeHistory
from tests.convert.formats.FusionCodec.Brep.Journal.JournalArchive import JournalArchive
from tests.convert.formats.FusionCodec.Brep.Round.TrimmedSources import KTrimmedSources


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("FileName,SurfaceCount", KTrimmedSources)
@TestMarks.parametrize("Reordered", (False, True))
def TestTrimRound(
    TmpPath: FilePath, FileName: str, SurfaceCount: int, Reordered: bool
) -> None:
    Original = NativeHistory(FileName)
    Native = ReadJournal(Original)
    Order = (
        0,
        *reversed(range(1, Native.ActiveCount)),
        *reversed(range(Native.ActiveCount, len(Native.Entities))),
    )
    Model = PermuteJournal(Native, Order) if Reordered else Native
    Payload = EmitJournal(Model)
    assert (Payload != Original) == Reordered
    Parsed = JournalArchive(TmpPath / "TrimmedRound.zip", Payload)
    assert Parsed == Model
    Surfaces = tuple(
        Index
        for Index, Value in enumerate(Parsed.Entities[: Parsed.ActiveCount])
        if isinstance(Value, (SphereNode, TorusNode))
    )
    assert len(Surfaces) == SurfaceCount
    Faces = tuple(
        Value
        for Value in Parsed.Entities[: Parsed.ActiveCount]
        if isinstance(Value, FaceNode) and Value.Surface in Surfaces
    )
    assert len(Faces) == SurfaceCount
    assert all(Value.FirstLoop >= 0 for Value in Faces)
