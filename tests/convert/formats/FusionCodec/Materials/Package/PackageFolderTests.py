from dataclasses import replace as ReplaceValue
from io import BytesIO as ByteStream
from uuid import UUID as UuidValue
from zipfile import ZipFile

from convert.formats.Fusion.MaterialCodec.Package.EmitPackage import EmitPackage
from convert.formats.Fusion.MaterialCodec.Package.Envelope.ReadLinks import ReadLinks
from convert.formats.Fusion.MaterialCodec.Package.Model.PackageCore import PackageCore
from convert.formats.Fusion.MaterialCodec.Package.Model.PackageFolder import (
    PackageFolder,
)
from convert.formats.Fusion.MaterialCodec.Package.Model.ResourceInfo import ResourceInfo
from convert.formats.Fusion.MaterialCodec.Package.ReadPackage import ReadPackage
from tests.convert.formats.FusionCodec.Materials.Package.NativePackage import (
    NativePackage,
)

KStamp = "2026-01-01T00:00:00Z"
KImage = b"\x89PNG\r\n\x1a\nkit"


def MakeCore(Number: int, NameValue: str) -> PackageCore:
    return PackageCore(str(UuidValue(int=Number)), KStamp, KStamp, 1, NameValue)


def MakeAsset(Number: int, NameValue: str) -> PackageFolder:
    LeafValue = PackageFolder(
        MakeCore(Number + 2, "0"),
        Links=(
            ResourceInfo(
                NameValue + "_png",
                NameValue + "_png",
                "application/octet-stream",
                KStamp,
            ),
        ),
        Contents=(KImage + NameValue.encode(),),
    )
    Middle = PackageFolder(MakeCore(Number + 1, "thumbnail"), (LeafValue,))
    return PackageFolder(MakeCore(Number, NameValue), (Middle,))


def MakeTree() -> PackageFolder:
    return PackageFolder(
        MakeCore(1, "Resources"), (MakeAsset(10, "second"), MakeAsset(20, "first"))
    )


def TestFolderWrite() -> None:
    Original = ReadPackage(NativePackage())
    assert Original.Resources is None
    Changed = ReplaceValue(Original, Resources=MakeTree())
    Payload = EmitPackage(Changed)
    Prefix = Changed.AssetCore.Identifier + "/Resources/"
    with ZipFile(ByteStream(Payload)) as Archive:
        Names = set(Archive.namelist())
        assert ReadLinks(Archive.read(Changed.AssetCore.Identifier + "/cnx.xml")) == (
            "AssetData",
            "Resources",
            "Schemas",
        )
        assert ReadLinks(Archive.read(Prefix + "cnx.xml")) == ("second", "first")
        for NameValue in ("second", "first"):
            Folder = Prefix + NameValue + "/"
            assert ReadLinks(Archive.read(Folder + "cnx.xml")) == ("thumbnail",)
            assert ReadLinks(Archive.read(Folder + "thumbnail/cnx.xml")) == ("0",)
            LeafPath = Folder + "thumbnail/0/"
            assert {LeafPath + "cnx.xml", LeafPath + "core.xml"} <= Names
            assert Folder + "core.xml" in Names
            assert Archive.read(LeafPath + NameValue + "_png") == (
                KImage + NameValue.encode()
            )
        assert len(Names) == 25 + 2 + 2 * 7
    assert ReadPackage(Payload) == Changed


def TestFolderDrop() -> None:
    Original = ReadPackage(NativePackage())
    Changed = ReplaceValue(Original, Resources=MakeTree())
    Restored = ReadPackage(EmitPackage(ReplaceValue(Changed, Resources=None)))
    assert Restored == Original
