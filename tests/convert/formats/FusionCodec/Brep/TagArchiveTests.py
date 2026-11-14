from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from zipfile import ZipFile

from pytest import mark as TestMarks, raises as RaiseError

from convert.formats.Fusion.BrepCodec.EmitHistory import EmitHistory
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.BrepCodec.ReadHistory import ReadHistory
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.convert.formats.FusionCodec.Brep.BreakTagLength import BreakTagLength
from tests.convert.formats.FusionCodec.Brep.SampleInputs import MakeSample


def TestTagArchive(TmpPath: FilePath) -> None:
    Sample = MakeSample()
    Primary = FeatureTag("face-200", (-(1 << 31), (1 << 31) - 1), -1, 1)
    TagsValue = ReplaceValue(Sample.TagSet, SideFace=Primary)
    Payload = EmitHistory(
        Sample.Model, Sample.Identity, TagsValue, Sample.History, Sample.Stamp
    )
    Target = TmpPath / "SignedTagFields.zip"
    with ZipFile(Target, "w") as Archive:
        Archive.writestr("Solved.smbh", Payload)
    with ZipFile(Target) as Archive:
        Parsed = ReadHistory(Archive.read("Solved.smbh"))
    assert Parsed.TagSet.SideFace == Primary
    assert Parsed.Identity == Sample.Identity
    assert (
        EmitHistory(
            Parsed.Model, Parsed.Identity, Parsed.TagSet, Parsed.History, Parsed.Stamp
        )
        == Payload
    )


@TestMarks.parametrize("OwnerKind", ("body", "face"))
def TestTagLength(TmpPath: FilePath, OwnerKind: str) -> None:
    Sample = MakeSample()
    Primary = FeatureTag("face-123456", (1701,))
    TagsValue = ReplaceValue(Sample.TagSet, SideFace=Primary)
    Payload = EmitHistory(
        Sample.Model, Sample.Identity, TagsValue, Sample.History, Sample.Stamp
    )
    PrimaryId = (
        str(Sample.Identity.OperationId) if OwnerKind == "body" else Primary.PrimaryId
    )
    Target = TmpPath / "BadTagLength.zip"
    with ZipFile(Target, "w") as Archive:
        Archive.writestr("Solved.smbh", BreakTagLength(Payload, PrimaryId))
    with ZipFile(Target) as Archive:
        with RaiseError(ValueError, match="primary identifier length"):
            _ = ReadHistory(Archive.read("Solved.smbh"))


def TestAuthorTags() -> None:
    Source = (
        FilePath(__file__).resolve().parents[5]
        / "re/Fusion/LocalOracle/Authored/ProductionExtrusion.f3d"
    )
    Payload = Source.read_bytes()
    Model = ReadDocument(Payload)
    History = Model.Bodies[0].History
    assert not isinstance(History, JournalModel)
    assert History.Identity.OperationId == 301
    assert History.Identity.SecondaryId == 4
    assert EmitParsed(Model) == Payload
