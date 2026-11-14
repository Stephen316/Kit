from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as TestMarks, raises as Raises

from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Snapshots.EmitSnapPart import (
    EmitSnapPart,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Snapshots.ReadSnapPart import (
    ReadSnapPart,
)
from tests.convert.formats.FusionCodec.Documents.Reading.AuxPartSource import (
    NativeAuxParts,
    StoreAuxPart,
)


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestSnapEdit(TmpPath: FilePath) -> None:
    PartValue = next(
        Value for Value in NativeAuxParts(0) if Value.Name.endswith(".smb")
    )
    Decoded = ReadSnapPart(PartValue)
    Snapshot = Decoded.Snapshot
    assert isinstance(Snapshot, PrismSnapshot)
    Faces = Snapshot.TagSet.Faces
    TagSet = ReplaceValue(
        Snapshot.TagSet,
        Faces=(ReplaceValue(Faces[0], PrimaryId="edited-bottom"), *Faces[1:]),
    )
    Edited = ReplaceValue(Decoded, Snapshot=ReplaceValue(Snapshot, TagSet=TagSet))
    Stored = StoreAuxPart(TmpPath / "EditedSnapshot.zip", EmitSnapPart(Edited))
    Reopened = ReadSnapPart(Stored)
    assert Reopened == Edited
    assert Stored.Payload != PartValue.Payload
    with Raises(ValueError, match="Trailing|trailing"):
        _ = ReadSnapPart(ReplaceValue(Stored, Payload=Stored.Payload + b"unexpected"))


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestSnapOwner(TmpPath: FilePath) -> None:
    PartValue = next(
        Value for Value in NativeAuxParts(0) if Value.Name.endswith(".smb")
    )
    Decoded = ReadSnapPart(StoreAuxPart(TmpPath / "NativeSnapshot.zip", PartValue))
    Snapshot = Decoded.Snapshot
    assert isinstance(Snapshot, PrismSnapshot)
    Profile = ReplaceValue(
        Snapshot.Profile, VertexOwners=(2, *Snapshot.Profile.VertexOwners[1:])
    )
    with Raises(ValueError, match="owner is not incident"):
        _ = EmitSnapPart(
            ReplaceValue(Decoded, Snapshot=ReplaceValue(Snapshot, Profile=Profile))
        )
