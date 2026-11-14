from pathlib import Path as FilePath

from pytest import mark as TestMarks, raises as Raises

from convert.formats.Fusion.BrepCodec.EmitHistory import EmitHistory
from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.formats.Fusion.BrepCodec.Prism.EmitPrismHist import EmitPrismHist
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.EmitBodyPart import EmitBodyPart
from convert.formats.Fusion.DocumentCodec.ReadBodyPart import ReadBodyPart
from tests.convert.formats.FusionCodec.Brep.Prism.PrismArchive import StorePrism
from tests.convert.formats.FusionCodec.Brep.Prism.PrismSample import MakePrism
from tests.convert.formats.FusionCodec.Brep.SampleInputs import MakeSample


@TestMarks.parametrize("Profile", ("cylinder", "prism"))
def TestHistoryPart(TmpPath: FilePath, Profile: str) -> None:
    if Profile == "prism":
        Sample = MakePrism()
        Payload = EmitPrismHist(
            Sample.Model, Sample.Identity, Sample.TagSet, Sample.History, Sample.Stamp
        )
    else:
        Cylinder = MakeSample()
        Payload = EmitHistory(
            Cylinder.Model,
            Cylinder.Identity,
            Cylinder.TagSet,
            Cylinder.History,
            Cylinder.Stamp,
        )
    Stored = StorePrism(TmpPath / "History.zip", Payload)
    Value = ReadBodyPart(ContainerPart("Breps.BlobParts/BREP.Integration.smbh", Stored))
    assert isinstance(
        Value.History, PrismHistory if Profile == "prism" else HistoryModel
    )
    assert EmitBodyPart(Value).Payload == Stored


@TestMarks.parametrize(
    "PartName",
    ("Breps.BlobParts/BREP.Snapshot.smb", "ProteinAssets.BlobParts/Asset.protein"),
)
def TestPartKinds(TmpPath: FilePath, PartName: str) -> None:
    Sample = MakePrism()
    Payload = EmitPrismHist(
        Sample.Model, Sample.Identity, Sample.TagSet, Sample.History, Sample.Stamp
    )
    Stored = StorePrism(TmpPath / "WrongRole.zip", Payload)
    with Raises(ValueError, match="Unsupported Fusion document part"):
        _ = ReadBodyPart(ContainerPart(PartName, Stored))
