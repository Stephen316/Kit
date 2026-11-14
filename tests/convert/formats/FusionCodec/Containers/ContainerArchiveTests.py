from dataclasses import replace as Replace
from pathlib import Path as FilePath
from zipfile import ZipFile

from pytest import mark as TestMarks

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.SegmentCodec.Manifest.ReadRootWire import ReadRootWire
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from tests.convert.formats.FusionCodec.Containers.MakeContainer import MakeContainer


@TestMarks.parametrize("Watermark", (3, 5, 7, 1024))
def TestArchiveFile(TmpPath: FilePath, Watermark: int) -> None:
    Original = MakeContainer()
    Value = Replace(
        Original,
        Asset=Replace(
            Original.Asset,
            NextSegmentId=Watermark,
            Properties=(("documentName", "Independent envelope λ"),),
        ),
    )
    Target = TmpPath / "Independent.f3d"
    _ = Target.write_bytes(EmitContainer(Value))
    with ZipFile(Target) as Archive:
        assert all(Entry.compress_type == 0 for Entry in Archive.infolist())
        assert "FusionAssetName[Active]/Breps.BlobParts/" in Archive.namelist()
        assert "FusionAssetName[Active]/ProteinAssets.BlobParts/" in Archive.namelist()
        RootValue = ReadRootWire(Archive.read("Manifest.dat"))
        assert RootValue.Title == Value.Document.TypeName
        assert RootValue.OpaqueIds == (
            Value.Document.DocumentId,
            Value.Document.CurrentVersion,
        )
        assert RootValue.OpaqueWords == (17, 709361728)
        for SlotValue in Value.Asset.Segments:
            Prefix = "FusionAssetName[Active]/" + SlotValue.UserName + "1/"
            assert Prefix in Archive.namelist()
            Metadata = ReadMetaWire(Archive.read(Prefix + "MetaStream.dat"))
            assert Metadata.Header.SegmentId == SlotValue.SegmentId
        assert Archive.read("Properties.dat") == bytes(4)
    with OpenFusionZip(Target.read_bytes()) as Archive:
        BulkData, Spans = Archive.ReadDesign()
        assert BulkData == Value.Streams[0].BulkData
        assert len(Spans) == 4
    Decoded = ReadContainer(Target.read_bytes())
    assert Decoded == Value
    _ = Target.write_bytes(EmitContainer(Decoded))
    assert ReadContainer(Target.read_bytes()) == Value


def TestSharedNames(TmpPath: FilePath) -> None:
    Original = MakeContainer()
    Slots = tuple(
        Replace(Entry, UserName="Shared") for Entry in Original.Asset.Segments
    )
    Value = Replace(Original, Asset=Replace(Original.Asset, Segments=Slots))
    Target = TmpPath / "Shared.f3d"
    _ = Target.write_bytes(EmitContainer(Value))
    with ZipFile(Target) as Archive:
        for Index in range(1, 4):
            assert (
                f"FusionAssetName[Active]/Shared{Index}/MetaStream.dat"
                in Archive.namelist()
            )
    assert ReadContainer(Target.read_bytes()) == Value
