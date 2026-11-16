from pathlib import Path as FilePath

from pytest import mark as TestMarks, raises as Raises

from convert.Formats.Fusion.BrepCodec.EmitHistory import EmitHistory
from convert.Formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.Formats.Fusion.BrepCodec.Prism.EmitPrismHist import EmitPrismHist
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.DocumentCodec.EmitBodyPart import EmitBodyPart
from convert.Formats.Fusion.DocumentCodec.ReadBodyPart import ReadBodyPart
from tests.Convert.Formats.FusionCodec.Brep.Prism.PrismArchive import StorePrism
from tests.Convert.Formats.FusionCodec.Brep.Prism.PrismSample import MakePrism
from tests.Convert.Formats.FusionCodec.Brep.SampleInputs import MakeSample


# the history part contract needs boundary coverage so stored document relationships remain consistent
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


# the part kinds contract needs boundary coverage so stored document relationships remain consistent
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
