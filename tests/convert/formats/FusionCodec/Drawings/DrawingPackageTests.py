from io import BytesIO
from zipfile import ZipFile

from pytest import importorskip as ImportSkip
from pytest import raises as ExpectError

from convert.formats.Fusion.DrawingCodec.Package.DrawingPackage import DrawingPackage
from convert.formats.Fusion.DrawingCodec.Package.EmitPackage import EmitPackage
from convert.formats.Fusion.DrawingCodec.Package.EntryLayout import EntryLayout
from convert.formats.Fusion.DrawingCodec.Package.PackageEntry import PackageEntry
from convert.formats.Fusion.DrawingCodec.Package.ReadPackage import ReadPackage

KFolderLayout = EntryLayout(0, 0x0800, 0x5A21, 0x5B6C, 63, 10, 16)

KStoredLayout = EntryLayout(0, 0x0800, 0x5A21, 0x5B6C, 63, 10, 0)

KDeflateLayout = EntryLayout(8, 0x0808, 0x6000, 0x5B6C, 20, 20, 0)

KZstdLayout = EntryLayout(93, 0x0800, 0x5A21, 0x5B6C, 63, 63, 0)


def SamplePackage(Method: EntryLayout) -> DrawingPackage:
    return DrawingPackage(
        (
            PackageEntry("Documentation[Active]/", b"", KFolderLayout),
            PackageEntry("Manifest.dat", b"root manifest" * 9, KStoredLayout),
            PackageEntry("Documentation[Active]/Données.json", b"{}" * 40, Method),
        )
    )


def InflateZstd(DataValue: bytes, SizeValue: int) -> bytes:
    Codec = ImportSkip("compression.zstd")
    Result = Codec.decompress(DataValue)
    assert isinstance(Result, bytes) and len(Result) == SizeValue
    return Result


def TestDeflate() -> None:
    Package = SamplePackage(KDeflateLayout)
    DataValue = EmitPackage(Package)
    assert ReadPackage(DataValue) == Package
    with ZipFile(BytesIO(DataValue)) as Archive:
        assert Archive.testzip() is None
        assert Archive.read("Manifest.dat") == b"root manifest" * 9
        InfoValue = Archive.getinfo("Documentation[Active]/Données.json")
        assert (InfoValue.flag_bits, InfoValue.compress_type) == (0x0808, 8)
        assert (InfoValue.create_version, InfoValue.extract_version) == (20, 20)


def TestZstdFrames() -> None:
    Codec = ImportSkip("compression.zstd")
    Package = SamplePackage(KZstdLayout)
    RawData = EmitPackage(Package)
    assert ReadPackage(RawData, InflateZstd) == Package
    Packed = EmitPackage(Package, Codec.compress)
    assert ReadPackage(Packed, InflateZstd) == Package
    with ExpectError(ValueError, match="require a decoder"):
        _ = ReadPackage(Packed)


def TestBadLayout() -> None:
    BadFlags = EntryLayout(8, 0x0001, 0, 0, 20, 20, 0)
    with ExpectError(ValueError, match="Unsupported"):
        _ = EmitPackage(SamplePackage(BadFlags))
    BadMethod = EntryLayout(12, 0x0800, 0, 0, 20, 20, 0)
    with ExpectError(ValueError, match="Unsupported"):
        _ = EmitPackage(SamplePackage(BadMethod))
    Folder = PackageEntry("Documentation[Active]/", b"x", KFolderLayout)
    with ExpectError(ValueError, match="directories must be empty"):
        _ = EmitPackage(DrawingPackage((Folder,)))
    Plain = EntryLayout(0, 0, 0, 0, 20, 20, 0)
    with ExpectError(ValueError, match="UTF flag"):
        _ = EmitPackage(DrawingPackage((PackageEntry("Données", b"", Plain),)))
    with ExpectError(ValueError, match="Invalid Fusion drawing package"):
        _ = EmitPackage(DrawingPackage(()))


def TestReadRejects() -> None:
    DataValue = EmitPackage(SamplePackage(KDeflateLayout))
    with ExpectError(ValueError, match="central directory"):
        _ = ReadPackage(DataValue + b"\x00")
    Damaged = bytearray(DataValue)
    Damaged[DataValue.index(b"root manifest")] ^= 0xFF
    with ExpectError(ValueError, match="CRC mismatch"):
        _ = ReadPackage(bytes(Damaged))
    Shifted = bytearray(DataValue)
    Shifted[10] ^= 0x01
    with ExpectError(ValueError, match="disagree"):
        _ = ReadPackage(bytes(Shifted))
    with ExpectError(ValueError, match="outside the supported range"):
        _ = ReadPackage(b"PK")
