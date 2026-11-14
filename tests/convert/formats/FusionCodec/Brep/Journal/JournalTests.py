from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import approx as Approx, mark as TestMarks

from convert.formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from tests.convert.formats.FusionCodec.Brep.Frustum.NativeHistory import NativeHistory
from tests.convert.formats.FusionCodec.Brep.Journal.JournalArchive import JournalArchive
from tests.convert.formats.FusionCodec.Brep.Journal.JournalSources import (
    KJournalSources,
)
from tests.convert.formats.FusionCodec.Brep.Journal.LiveCarriers import LiveCarriers


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("SourcePath,EntityCount", KJournalSources)
def TestJournalFile(TmpPath: FilePath, SourcePath: str, EntityCount: int) -> None:
    Payload = NativeHistory(SourcePath)
    Native = ReadJournal(Payload)
    assert Native.ActiveCount == 35 and len(Native.Entities) == EntityCount
    assert tuple(State.StateId for State in Native.States) == (14, 2, 9)
    States = Materialize(Native)
    assert tuple(State.StateId for State in States) == (14, 9, 2)
    assert tuple(len(State.Versions) for State in States) == (35, 36, 1)
    assert {
        Value.TrackedId for Value in Native.Entities if isinstance(Value, TrackAttrib)
    } == {271}
    Carriers = LiveCarriers(Native)
    assert len(Carriers) == 2 and Carriers[1].MajorAxisCm == Approx((1.0, 0.0, 0.0))
    assert Carriers[1].SineAngle == 0.0
    assert EmitJournal(Native) == Payload
    Parsed = JournalArchive(TmpPath / "ReconstructedJournal.zip", EmitJournal(Native))
    assert Parsed == Native and Materialize(Parsed) == States
