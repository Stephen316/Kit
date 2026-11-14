from dataclasses import replace as Replace
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from zipfile import ZipFile

from pytest import mark as TestMarks, raises as RaiseError

from convert.formats.Fusion.BrepCodec.EmitHistory import EmitHistory
from convert.formats.Fusion.BrepCodec.History.InsertState import MakeInsertState
from convert.formats.Fusion.BrepCodec.History.Preamble import MakePreamble
from convert.formats.Fusion.BrepCodec.ReadHistory import ReadHistory
from convert.formats.Fusion.BrepCodec.Reading.ReadBrepWire import ReadBrepWire
from convert.formats.Fusion.BrepCodec.Reading.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.Wire.EmitBrepRecord import EmitBrepRecord
from tests.convert.formats.FusionCodec.Brep.SampleInputs import MakeSample

KRepoRoot = FilePath(__file__).resolve().parents[5]


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestRolledState(TmpPath: FilePath) -> None:
    Source = KRepoRoot / "re/Fusion/Study/timeline-5867579925b5/rolled_back.f3d"
    with ZipFile(Source) as Archive:
        Names = tuple(
            NameValue for NameValue in Archive.namelist() if NameValue.endswith(".smbh")
        )
        assert len(Names) == 1
        Stream = ReadBrepWire(Archive.read(Names[0]), True)
    History = ReadJournal(Stream.Journal, len(Stream.Table.Records))
    assert History.CurrentId == History.CurrentStateId == 3
    assert History.MaxStateId == 10
    assert History.InitialId == 2
    assert History.NextEntityTag == 6
    assert History.BoardStatus == 2
    Sample = MakeSample()
    Identity = Replace(Sample.Identity, BodyKey=0)
    Target = TmpPath / "PreservedState.smbh"
    _ = Target.write_bytes(
        EmitHistory(Sample.Model, Identity, Sample.TagSet, History, Sample.Stamp)
    )
    assert ReadHistory(Target.read_bytes()).History == History


@TestMarks.parametrize("Status", (-1, 4, 1 << 31))
def TestBoardStatus(TmpPath: FilePath, Status: int) -> None:
    Sample = MakeSample()
    Payload = EmitHistory(
        Sample.Model, Sample.Identity, Sample.TagSet, Sample.History, Sample.Stamp
    )
    Current = MakeInsertState(Sample.History, 35)
    Fields = list(Current.Fields)
    Fields[11] = Status
    Original = EmitBrepRecord(Current)
    assert Payload.count(Original) == 1
    Payload = Payload.replace(
        Original, EmitBrepRecord(Replace(Current, Fields=tuple(Fields))), 1
    )
    Target = TmpPath / "InvalidStatus.smbh"
    _ = Target.write_bytes(Payload)
    with RaiseError(ValueError, match="bulletin board status"):
        _ = ReadHistory(Target.read_bytes())


@TestMarks.parametrize("Maximum", (16, 1 << 31))
def TestStateLimit(TmpPath: FilePath, Maximum: int) -> None:
    Sample = MakeSample()
    Payload = EmitHistory(
        Sample.Model, Sample.Identity, Sample.TagSet, Sample.History, Sample.Stamp
    )
    Preamble = MakePreamble(Sample.History)
    Fields = list(Preamble.Fields)
    Fields[1] = Maximum
    Original = EmitBrepRecord(Preamble)
    assert Payload.count(Original) == 1
    Payload = Payload.replace(
        Original, EmitBrepRecord(Replace(Preamble, Fields=tuple(Fields))), 1
    )
    Target = TmpPath / "InvalidMaximum.smbh"
    _ = Target.write_bytes(Payload)
    with RaiseError(ValueError, match="history metadata|maximum state ID"):
        _ = ReadHistory(Target.read_bytes())
