from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import approx as ApproxValue, mark as TestMarks
from convert.formats.Fusion.BrepCodec.Models.SnapshotModel import SnapshotModel

from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Snapshots.EmitSnapPart import (
    EmitSnapPart,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Snapshots.ReadSnapPart import (
    ReadSnapPart,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmPrism import ReadAsmPrism
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable
from tests.convert.formats.FusionCodec.Documents.Reading.AuxPartSource import (
    NativeAuxParts,
    StoreAuxPart,
)


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize("SourceIndex,Volume", ((0, 30.0), (1, 14.467), (2, None)))
def TestSnapshot(TmpPath: FilePath, SourceIndex: int, Volume: float | None) -> None:
    PartValue = next(
        Value for Value in NativeAuxParts(SourceIndex) if Value.Name.endswith(".smb")
    )
    Decoded = ReadSnapPart(PartValue)
    Stored = StoreAuxPart(TmpPath / "Snapshot.zip", EmitSnapPart(Decoded))
    Reopened = ReadSnapPart(Stored)
    assert Reopened == Decoded
    Table = ReadAsmTable(Stored.Payload)
    assert Table.RootCount == 4
    assert tuple(Record.Name for Record in Table.Records[:4]) == (
        "asmheader",
        "body",
        "body",
        "body",
    )
    Snapshot = Reopened.Snapshot
    if isinstance(Snapshot, PrismSnapshot):
        assert len(Table.Records) == 168
        assert len(ReadAsmPrism(Table, 1, 4).Rings) == 6
        assert (
            Snapshot.Model.Width * Snapshot.Model.Depth * Snapshot.Model.Height / 1000
            == ApproxValue(Volume)
        )
        for Region in (Snapshot.Profile, Snapshot.Sketch):
            assert set(Region.CornersCm) == set(Snapshot.Frame.CornersCm[:4])
            assert len({Value.PrimaryId for Value in Region.CoedgeTags}) == 4
    else:
        assert isinstance(Snapshot, SnapshotModel)
        assert len(Table.Records) == 59
        assert Snapshot.Model.Height == ApproxValue(7.0)
