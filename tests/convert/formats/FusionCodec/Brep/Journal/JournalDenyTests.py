from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as TestMarks, raises as RaisesError

from tests.convert.formats.FusionCodec.Brep.Frustum.NativeHistory import NativeHistory
from tests.convert.formats.FusionCodec.Brep.Journal.JournalArchive import JournalArchive
from tests.convert.formats.FusionCodec.Brep.Journal.PoisonJournal import PoisonJournal


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize(
    "Fault", ("trailing", "attribute", "reference", "status", "cycle", "initial-board")
)
def TestJournalDeny(TmpPath: FilePath, Fault: str) -> None:
    Payload = NativeHistory("re/Fusion/Study/moretools-88a2cd6cad0b/Draft.f3d")
    Changed = PoisonJournal(Payload, Fault)
    assert Changed != Payload
    with RaisesError(ValueError):
        _ = JournalArchive(TmpPath / "MalformedHistory.zip", Changed)
