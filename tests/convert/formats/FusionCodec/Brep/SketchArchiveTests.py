from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from zipfile import ZipFile

from pytest import mark as TestMarks, raises as RaiseError

from convert.formats.Fusion.BrepCodec.EmitHistory import EmitHistory
from convert.formats.Fusion.BrepCodec.EmitSnapshot import EmitSnapshot
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.BrepCodec.ReadHistory import ReadHistory
from convert.formats.Fusion.BrepCodec.ReadSnapshot import ReadSnapshot
from convert.formats.Fusion.GeometryCodec.EncodeSmbString import EncodeSmbString
from tests.convert.formats.FusionCodec.Brep.SampleInputs import MakeSample


def TestSketchZip(TmpPath: FilePath) -> None:
    Sample = MakeSample()
    Sketch = SketchLink((1 << 64) - 1, (1 << 63) + 37, (1 << 32) - 1, 4, 4)
    TagsValue = ReplaceValue(Sample.TagSet, Sketch=Sketch)
    History = EmitHistory(
        Sample.Model, Sample.Identity, TagsValue, Sample.History, Sample.Stamp
    )
    Snapshot = EmitSnapshot(Sample.Model, TagsValue, Sample.Stamp)
    Target = TmpPath / "SketchIdentities.zip"
    with ZipFile(Target, "w") as Archive:
        Archive.writestr("History.smbh", History)
        Archive.writestr("Snapshot.smb", Snapshot)
    with ZipFile(Target) as Archive:
        ParsedHistory = ReadHistory(Archive.read("History.smbh"))
        ParsedSnapshot = ReadSnapshot(Archive.read("Snapshot.smb"))
    assert ParsedHistory.TagSet.Sketch == Sketch
    assert ParsedSnapshot.TagSet.Sketch == Sketch


@TestMarks.parametrize("SplitPair", ("0 2", "3 2", "1 0"))
def TestSketchRange(TmpPath: FilePath, SplitPair: str) -> None:
    Sample = MakeSample()
    Sketch = SketchLink(901, 0, 0, 1, 2)
    TagsValue = ReplaceValue(Sample.TagSet, Sketch=Sketch)
    Payload = EmitHistory(
        Sample.Model, Sample.Identity, TagsValue, Sample.History, Sample.Stamp
    )
    Original = EncodeSmbString(7, "901 0 0 0 1 2")
    Altered = EncodeSmbString(7, "901 0 0 0 " + SplitPair)
    assert Payload.count(Original) == 2
    Target = TmpPath / "BadSketchSplit.zip"
    with ZipFile(Target, "w") as Archive:
        Archive.writestr("History.smbh", Payload.replace(Original, Altered, 1))
    with ZipFile(Target) as Archive:
        with RaiseError(ValueError, match="sketch split"):
            _ = ReadHistory(Archive.read("History.smbh"))
