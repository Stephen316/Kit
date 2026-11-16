from hashlib import sha256 as HashBytes
from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import TypedDict, cast as CastValue

import pytest as Pytest

from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.RectanglePart import ReadRectPart
from tests.Research.Archives.SolidWorksEndVerify import VerifyListEnd

# paths and offsets pin the independent rectangle controls and their typed end
KCapturePath = (
    FilePath(__file__).resolve().parents[3]
    / "re/automation/PairedCaptures/P01/solidworks-75b9308cf13e"
)

# the source receipt binds the exact native bytes independently of the footer encoder
KReceiptHash = "3c389fe4069bece7ecf64f0294d111ce7f44131b2fc576d3f2ac4291e0fec7bf"


# the fixture binds each selected file to the native receipt and observed byte size
class NativeEntry(TypedDict):
    file: str
    size_bytes: int
    sha256: str


# only the pinned native file inventory is needed to select the right input
class NativeReceipt(TypedDict):
    native_files: list[NativeEntry]


# the whole native profile reader must reach the independently generated footer
@Pytest.mark.parametrize(
    ("Variant", "EndOffset"),
    (
        ("baseline-a", 11895),
        ("baseline-b", 12125),
        ("edit-width_mm-41", 12125),
        ("edit-height_mm-23", 12125),
        ("units-inch", 12125),
        ("plane-yz", 11967),
    ),
)
def CheckSwListEnd(Variant: str, EndOffset: int) -> None:
    ReceiptBytes = (KCapturePath / "receipt.json").read_bytes()
    assert HashBytes(ReceiptBytes).hexdigest() == KReceiptHash
    Receipt = CastValue(NativeReceipt, LoadJson(ReceiptBytes))
    NameValue = f"P01-solidworks-{Variant}.SLDPRT"
    (Entry,) = [
        Value for Value in Receipt["native_files"] if Value["file"] == NameValue
    ]
    RawValue = (KCapturePath / NameValue).read_bytes()
    assert (len(RawValue), HashBytes(RawValue).hexdigest()) == (
        Entry["size_bytes"],
        Entry["sha256"],
    )
    Archive = SldprtArchive.from_bytes(RawValue)
    Generation = ContainerMo(Archive.streams)
    assert Generation == 19000
    Config = Archive.require("Contents/Config-0")
    Resolved = Archive.require("Contents/Config-0-ResolvedFeatures")
    assert FieldCursor(Resolved, 0).ReadInts("<iH") == (106, 18)
    Original = ReadRectPart(Config, Resolved, Generation)
    with Pytest.MonkeyPatch.context() as PatchValue:
        Footer = VerifyListEnd(PatchValue, Resolved, Generation, EndOffset)
    assert ReadRectPart(Config, Resolved[:EndOffset] + Footer, Generation) == Original
