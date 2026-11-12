from io import BytesIO
from struct import unpack_from as UnpackFrom
from zipfile import ZipFile
from zlib import crc32 as CrcValue

from pytest import MonkeyPatch as PatchContext
from pytest import importorskip as ImportSkip, mark as TestMarks, raises as Raises

from convert.adapters.Fusion.ArchiveProbe import ProbeFusion
from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.AssetCodec.Zip.EmitAssetZip import EmitAssetZip
from convert.formats.Fusion.AssetCodec.Zip.ZipAssetRow import ZipAssetRow

# exact active paths exercise the normal fusion container probe
KActiveRoot = "FusionAssetName[Active]/"

# local and central entries must carry the same standard utf filename flag
KUtfZipFlag = 0x0800


# independent decompression exercises the callback used by older sdk runtimes
def InflateZstd(DataValue: bytes, ExpectedSize: int) -> bytes:
    Codec = ImportSkip("compression.zstd")
    Result = Codec.decompress(DataValue)
    assert isinstance(Result, bytes)
    assert len(Result) == ExpectedSize
    return Result


# seekable output keeps local boundaries identical to central membership
def TestZipLayout() -> None:
    Prefix = KActiveRoot + "FusionDesignSegmentType1/"
    Members = (
        ZipAssetRow(KActiveRoot, b"", False),
        ZipAssetRow(Prefix, b"", False),
        ZipAssetRow("Manifest.dat", b"root", True),
        ZipAssetRow(Prefix + "BulkStream.dat", b"design", True),
        ZipAssetRow(Prefix + "MetaStream.dat", b"metadata", True),
        ZipAssetRow(KActiveRoot + "Données.txt", b"portable", False),
    )
    DataValue = EmitAssetZip(Members)
    assert DataValue == EmitAssetZip(Members)
    assert ProbeFusion(DataValue).confidence == 1.0
    with ZipFile(BytesIO(DataValue)) as Archive:
        Entries = Archive.infolist()
        assert Archive.namelist() == [Member.Name for Member in Members]
        Bounds = [Entry.header_offset for Entry in Entries[1:]] + [Archive.start_dir]
        assert (Entries[0].header_offset, Archive.comment) == (0, b"")
        for Entry, Member, Boundary in zip(Entries, Members, Bounds, strict=True):
            LocalFields = UnpackFrom("<I5H3I2H", DataValue, Entry.header_offset)
            NameStart = Entry.header_offset + 30
            NameEnd = NameStart + LocalFields[-2]
            assert LocalFields == (
                0x04034B50,
                Entry.extract_version,
                KUtfZipFlag,
                93 if Member.UseZstd else 0,
                0,
                33,
                CrcValue(Member.Data),
                Entry.compress_size,
                len(Member.Data),
                len(Member.Name.encode("utf-8")),
                0,
            )
            assert Entry.flag_bits == KUtfZipFlag
            assert Entry.extra == Entry.comment == b""
            assert (Entry.create_system, Entry.create_version) == (3, 46)
            assert DataValue[NameStart:NameEnd].decode() == Member.Name
            assert NameEnd + Entry.compress_size == Boundary
            if Entry.is_dir():
                assert Entry.external_attr == (0o40755 << 16) | 0x10
                assert Entry.file_size == Entry.compress_size == 0
            else:
                assert Entry.external_attr == 0o100644 << 16
            if not Member.UseZstd:
                assert Archive.read(Entry) == Member.Data
        Footer = UnpackFrom("<I4H2IH", DataValue, len(DataValue) - 22)
        assert Footer == (
            0x06054B50,
            0,
            0,
            len(Entries),
            len(Entries),
            len(DataValue) - 22 - Archive.start_dir,
            Archive.start_dir,
            0,
        )


# frame sizes span every content field width and both window layouts
@TestMarks.parametrize(
    "DataSize", (0, 1, 255, 256, 65791, 65792, 131072, 131073, 262145)
)
def TestZipFrames(DataSize: int) -> None:
    Pattern = bytes(range(256))
    Payload = (Pattern * ((DataSize + 255) // 256))[:DataSize]
    DataValue = EmitAssetZip((ZipAssetRow("entry.dat", Payload, True),))
    Codec = ImportSkip("compression.zstd")
    with ZipFile(BytesIO(DataValue)) as Archive:
        Entry = Archive.getinfo("entry.dat")
        DataStart = 30 + len(Entry.filename)
        FrameData = DataValue[DataStart : DataStart + Entry.compress_size]
        assert FrameData[:4] == b"\x28\xb5\x2f\xfd"
        assert Codec.decompress(FrameData) == Payload
        assert Archive.read(Entry) == Payload
    with OpenFusionZip(DataValue, InflateZstd) as Archive:
        assert Archive.ReadMember("entry.dat", DataSize) == Payload


# a structurally decompressible raw payload still requires the independent zip crc
def TestZipCorrupt() -> None:
    ImportSkip("compression.zstd")
    DataValue = bytearray(EmitAssetZip((ZipAssetRow("entry.dat", b"value", True),)))
    with ZipFile(BytesIO(DataValue)) as Archive:
        DataValue[Archive.start_dir - 1] ^= 1
    with OpenFusionZip(bytes(DataValue), InflateZstd) as Archive:
        with Raises(ValueError, match="size or CRC mismatch"):
            _ = Archive.ReadMember("entry.dat", 5)
    DataValue[6] ^= 0x08
    with OpenFusionZip(bytes(DataValue), InflateZstd) as Archive:
        with Raises(ValueError, match="local and central entries disagree"):
            _ = Archive.ReadMember("entry.dat", 5)


# portable member names must be exact paths without aliases or special files
@TestMarks.parametrize(
    "NameValue",
    (
        "",
        "/",
        "/file",
        "../file",
        "a/./file",
        "a//file",
        "a//",
        "C:/file",
        "a\\file",
        "a\x00b",
        "a\n",
        "con.txt",
        "COM¹",
        "dir. /file",
        "item.",
        "name?",
        "e\u0301",
        "a" * 256,
        "/".join(("a",) * 65),
    ),
)
def TestZipBadName(NameValue: str) -> None:
    with Raises(ValueError, match="Unsafe"):
        _ = EmitAssetZip((ZipAssetRow(NameValue, b"", False),))


# path aliases and nonempty directories cannot be repaired by zip metadata
@TestMarks.parametrize(
    "Members",
    (
        (ZipAssetRow("dir/", b"x", False),),
        (ZipAssetRow("dir/", b"", True),),
        (ZipAssetRow("entry", b"", False), ZipAssetRow("entry", b"", True)),
        (ZipAssetRow("Name", b"", False), ZipAssetRow("name", b"", False)),
        (ZipAssetRow("dir", b"", False), ZipAssetRow("dir/", b"", False)),
        (ZipAssetRow("dir", b"", False), ZipAssetRow("dir/item", b"", False)),
    ),
)
def TestZipBadRows(Members: tuple[ZipAssetRow, ...]) -> None:
    with Raises(ValueError):
        _ = EmitAssetZip(Members)


# preflight must reject each bound before producing an incomplete archive
def TestZipLimits(MonkeyPatch: PatchContext) -> None:
    with Raises(ValueError, match="entry count"):
        _ = EmitAssetZip(())
    Member = ZipAssetRow("entry", b"data", False)
    MonkeyPatch.setattr(
        "convert.formats.Fusion.AssetCodec.Zip.PlanZipRows.KMaxZipEntries", 1
    )
    with Raises(ValueError, match="entry count"):
        _ = EmitAssetZip((Member, Member))
    MonkeyPatch.setattr(
        "convert.formats.Fusion.AssetCodec.Zip.PlanZipRow.KMaxMemberBytes", 3
    )
    with Raises(ValueError, match="member exceeds size limit"):
        _ = EmitAssetZip((Member,))
    MonkeyPatch.setattr(
        "convert.formats.Fusion.AssetCodec.Zip.PlanZipRow.KMaxMemberBytes", 12
    )
    with Raises(ValueError, match="encoded member exceeds size limit"):
        _ = EmitAssetZip((ZipAssetRow(Member.Name, Member.Data, True),))
    MonkeyPatch.setattr(
        "convert.formats.Fusion.AssetCodec.Zip.PlanZipRows.KMaxArchiveSize", 111
    )
    with Raises(ValueError, match="archive exceeds size limit"):
        _ = EmitAssetZip((Member,))
    MonkeyPatch.setattr(
        "convert.formats.Fusion.AssetCodec.Zip.PlanZipRows.KMaxCentralSize", 50
    )
    with Raises(ValueError, match="central directory exceeds limit"):
        _ = EmitAssetZip((Member,))
