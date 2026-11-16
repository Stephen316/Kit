from pathlib import Path as FilePath

from pytest import mark as TestMarks, raises as Raises

from convert.Formats.Fusion.BrepCodec.Prism.EmitPrismHist import EmitPrismHist
from convert.Formats.Fusion.BrepCodec.Prism.ReadPrismHist import ReadPrismHist
from tests.Convert.Formats.FusionCodec.Brep.Prism.PrismArchive import StorePrism
from tests.Convert.Formats.FusionCodec.Brep.Prism.PrismSample import MakePrism


# the prism reject contract needs boundary coverage so stored document relationships remain consistent
@TestMarks.parametrize("Damage", ("trailing", "attribute", "truncated"))
def TestPrismReject(TmpPath: FilePath, Damage: str) -> None:
    Sample = MakePrism()
    Payload = EmitPrismHist(
        Sample.Model, Sample.Identity, Sample.TagSet, Sample.History, Sample.Stamp
    )
    if Damage == "trailing":
        Payload += b"extra"
    elif Damage == "attribute":
        Payload = Payload.replace(
            b"generic_tag_attrib_def ", b"generic_tag_attrib_bad ", 1
        )
    else:
        Payload = Payload[:-1]
    Stored = StorePrism(TmpPath / "Damaged.zip", Payload)
    with Raises(ValueError):
        _ = ReadPrismHist(Stored)
