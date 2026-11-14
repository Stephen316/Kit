from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as TestMarks

from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.formats.Fusion.BrepCodec.Journal.PermuteJournal import PermuteJournal
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
def TestPermutation(TmpPath: FilePath, SourcePath: str, EntityCount: int) -> None:
    Payload = NativeHistory(SourcePath)
    Native = ReadJournal(Payload)
    Order = (
        0,
        *reversed(range(1, Native.ActiveCount)),
        *reversed(range(Native.ActiveCount, EntityCount)),
    )
    Changed = PermuteJournal(Native, Order)
    Encoded = EmitJournal(Changed)
    Parsed = JournalArchive(TmpPath / "PermutedJournal.zip", Encoded)
    assert Encoded != Payload and Parsed == Changed
    assert Parsed.Stream == Native.Stream
    assert tuple(State.StateId for State in Materialize(Parsed)) == (14, 9, 2)
    assert tuple(len(State.Versions) for State in Materialize(Parsed)) == (35, 36, 1)
    assert tuple(
        (Value.OriginCm, Value.MajorAxisCm, Value.SineAngle)
        for Value in LiveCarriers(Parsed)
    ) == tuple(
        (Value.OriginCm, Value.MajorAxisCm, Value.SineAngle)
        for Value in LiveCarriers(Native)
    )
    assert sorted(
        repr(Value.Groups) for Value in Parsed.Entities if isinstance(Value, TagAttrib)
    ) == sorted(
        repr(Value.Groups) for Value in Native.Entities if isinstance(Value, TagAttrib)
    )
