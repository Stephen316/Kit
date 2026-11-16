from hashlib import sha256 as HashBytes
from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import Protocol, TypedDict, cast as CastValue

import pytest as Pytest

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.Geometry.Parasolid import DecodePartMut, ParaHeaderData, ScanPartRecords
from interchange.geometry.Models.VectorSpace import SpaceVector
from tests.Research.Archives.SolidWorksDistCodecs import LoadResearchMut

# the discovery receipt independently pins every archive in the first rectangle lane
KCapturePath = (
    FilePath(__file__).resolve().parents[3]
    / "re/automation/PairedCaptures/P01/solidworks-75b9308cf13e"
)

# the exact receipt fixes source size digest and identity
KReceiptHash = "3c389fe4069bece7ecf64f0294d111ce7f44131b2fc576d3f2ac4291e0fec7bf"

# the side partition owns the ghost point and its value node
KGhostStream = "Contents/Config-0-GhostPartition"


# the receipt keeps each archive bound to a file name and exact bytes
class NativeEntry(TypedDict):
    file: str
    size_bytes: int
    sha256: str


# the file inventory is sufficient to select an exact input to the hosted comparison
class NativeReceipt(TypedDict):
    native_files: list[NativeEntry]


# the research module stays outside the installed package during hosted verification
class GhostCodec(Protocol):

    # the caller supplies the enclosing graph allocation
    def GhostAllocation(self, *Values: int) -> object: ...

    # each returned byte span has its own independent position in the partition graph
    def EncodeGhostRows(
        self, PointMm: SpaceVector, Slots: object, GhostId: int, *, Schema: str
    ) -> tuple[bytes, bytes, bytes]: ...


# open and check the exact vendor authored archive before locating ghost rows
def OpenGhostPart(Variant: str) -> bytes:
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
    (Payload,) = DecodePartMut(Archive.require(KGhostStream), KGhostStream)
    assert Payload.kind == "partition"
    return Payload.data


# the checked archive joins the real point and vertex before comparing output bytes
@Pytest.mark.parametrize(
    "Variant",
    (
        "baseline-a",
        "baseline-b",
        "edit-width_mm-41",
        "edit-height_mm-23",
        "units-inch",
        "plane-yz",
    ),
)
def CheckGhostPoint(Variant: str) -> None:
    Payload = OpenGhostPart(Variant)
    Header = ParaHeaderData(Payload)
    assert Header is not None
    Tables = ScanPartRecords(Payload[Header.body_offset :])
    assert Tables is not None
    (Point,) = Tables.points.values()
    (Vertex,) = Tables.vertex_uses.values()
    assert (Point.attribute, Vertex.attribute, Point.point) == (
        8,
        10,
        SpaceVector(0, 0, 0),
    )
    assert (Point.references, Vertex.references) == ((1, 10, 1, 1), (1, 1, 1, 1, 8))
    with Pytest.MonkeyPatch.context() as PatchValue:
        Codec = CastValue(
            GhostCodec, LoadResearchMut(PatchValue, "Partition.PointRows")
        )
        Slots = Codec.GhostAllocation(6, 7, 9, 11, 4, 2)
        Encoded = Codec.EncodeGhostRows(
            SpaceVector(0, 0, 0), Slots, 10001, Schema=Header.schema
        )
    assert Encoded == (
        Payload[0x3B5:0x3DE],
        Payload[0x414:0x431],
        Payload[0x488:0x495],
    )
