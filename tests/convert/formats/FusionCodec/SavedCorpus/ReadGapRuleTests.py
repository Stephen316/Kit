from io import BytesIO
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from uuid import UUID as UuidValue
from zipfile import ZipFile

from pytest import mark as TestMarks, raises as ExpectError

from convert.adapters.Fusion.Projection.NativeMaterial import NativeMaterial
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Auxiliary.Images.CheckImagePart import (
    CheckImagePart,
)
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.EntityCodec.Wire.FlagByte import EmitFlag, ReadFlagMut
from convert.formats.Fusion.MaterialCodec.Package.Model.PackageCore import PackageCore
from convert.formats.Fusion.MaterialCodec.Package.Model.PackageFolder import (
    PackageFolder,
)
from convert.formats.Fusion.MaterialCodec.Package.Validation.CheckFolder import (
    CheckFolder,
)
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.Model.KnotSurface import KnotSurface
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

KRoot = FilePath(__file__).resolve().parents[5]

KRequiresCodec = TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)

KOracle = "re/Fusion/LocalOracle/"


def ReadCorpus(RelativeName: str) -> bytes:
    return (KRoot / RelativeName).read_bytes()


def TestFlagBytes() -> None:
    assert ReadFlagMut(MetaCursor(b"\x00")) is False
    assert ReadFlagMut(MetaCursor(b"\x01")) is True
    assert ReadFlagMut(MetaCursor(b"\x20")) == 0x20
    assert EmitFlag(True) == b"\x01"
    assert EmitFlag(0x20) == b"\x20"
    for Value in (1, 256, 0.5):
        with ExpectError(ValueError, match="flag requires"):
            _ = EmitFlag(Value)


@KRequiresCodec
def TestNarrowAsm() -> None:
    Model = ReadDocument(ReadCorpus("re/Fusion/examples/.f3d/example2.f3d"))
    Widths = {
        BodyValue.History.Header.IntWidth
        for BodyValue in Model.Bodies
        if isinstance(BodyValue.History, JournalModel)
    }
    assert Widths == {4}
    assert ReadDocument(EmitParsed(Model)) == Model


@KRequiresCodec
@TestMarks.parametrize(
    "RelativeName",
    (
        "ActSlack/Saves/FreshFirst.f3d",
        "Allocation/empty.f3d",
    ),
)
def TestDefaultMat(RelativeName: str) -> None:
    Model = ReadDocument(ReadCorpus(KOracle + RelativeName))
    assert not Model.Bodies
    SpecValue = NativeMaterial(Model)
    assert SpecValue != MaterialSpec()
    assert SpecValue.NameValue == ""
    assert SpecValue.Density == 7850.0


@KRequiresCodec
def TestAbsentMat() -> None:
    Model = ReadDocument(ReadCorpus(KOracle + "Authored/ProductionExtrusion.f3d"))
    assert Model.Bodies
    with ExpectError(ValueError, match="undefined physical material"):
        _ = NativeMaterial(Model)


@KRequiresCodec
def TestStaleForm() -> None:
    Model = ReadDocument(ReadCorpus(KOracle + "FormDocuments/Stale/BoxBrepMoved.f3d"))
    with ExpectError(ValueError, match="absent from its parts"):
        _ = EmitParsed(Model)


@KRequiresCodec
def TestAppleTorus() -> None:
    Model = ReadDocument(
        ReadCorpus(KOracle + "FeatureAuthoring/Authored/vendor_RoundRimChain.f3d")
    )
    assert ReadDocument(EmitParsed(Model)) == Model


@KRequiresCodec
def TestEdgeKnots() -> None:
    Archive = ZipFile(
        BytesIO(ReadCorpus(KOracle + "FormDocuments/Intervals/Box/Single.f3d"))
    )
    Members = [
        MemberName for MemberName in Archive.namelist() if MemberName.endswith(".tsm")
    ]
    assert len(Members) == 1
    Surface = ReadTspline(Archive.read(Members[0]))
    assert isinstance(Surface, KnotSurface)
    assert len(Surface.EdgeKnots) == len(Surface.Topology.Edges)
    assert ReadTspline(EmitTspline(Surface)) == Surface


def ImageMember() -> DocumentModel:
    Bundle = ReadBundle(ReadCorpus("re/Fusion/examples/.f3z/example1.f3z"))
    for Entry in Bundle.Documents:
        Names = ZipFile(BytesIO(Entry.DataValue)).namelist()
        if any("Images.BlobParts/Image." in MemberName for MemberName in Names):
            return ReadDocument(Entry.DataValue)
    raise AssertionError("example bundle lacks image parts")


@KRequiresCodec
def TestImageParts() -> None:
    Model = ImageMember()
    assert len(Model.Images) == 2
    assert all(Image.Payload.startswith(b"\x89PNG") for Image in Model.Images)
    Package = Model.Materials[0].Package
    assert Package.Resources is not None
    assert Package.Resources.Core.NameValue == "Resources"
    Identities = [Asset.DefinitionId for Asset in Package.Assets]
    assert len(set(Identities)) < len(Identities)
    assert ReadDocument(EmitParsed(Model)) == Model


def TestImageName() -> None:
    Valid = "Images.BlobParts/Image." + str(UuidValue(int=1)) + ".png"
    Payload = b"\x89PNG\r\n\x1a\n" + bytes(4)
    assert CheckImagePart(ContainerPart(Valid, Payload)).Name == Valid
    with ExpectError(ValueError, match="part name"):
        _ = CheckImagePart(ContainerPart("Images.BlobParts/Image.png", Payload))
    with ExpectError(ValueError, match="PNG payload"):
        _ = CheckImagePart(ContainerPart(Valid, bytes(12)))


def TestFolderRule() -> None:
    Stamp = "2026-01-01T00:00:00Z"
    CoreValue = PackageCore(str(UuidValue(int=1)), Stamp, Stamp, 1, "Resources")
    with ExpectError(ValueError, match="folders or resources"):
        CheckFolder(PackageFolder(CoreValue), 0)
    ChildCore = PackageCore(str(UuidValue(int=2)), Stamp, Stamp, 1, "../x")
    with ExpectError(ValueError, match="folder name"):
        CheckFolder(PackageFolder(CoreValue, (PackageFolder(ChildCore),)), 0)
