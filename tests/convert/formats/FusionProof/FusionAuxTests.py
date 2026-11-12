from typing import cast as CastValue
from hashlib import sha256 as ShaDigest
from io import BytesIO
from struct import pack as PackData, unpack_from as UnpackFrom
from zipfile import ZipFile

from pytest import raises as Raises

from convert.formats.Fusion.ArchiveRead.ArchiveMember import ArchiveMember
from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Auxiliary.ReadAuxFrame import ReadAuxFrame
from convert.formats.Fusion.SourceProof.Auxiliary.ReadAuxProof import ReadAuxProof
from convert.formats.Fusion.SourceProof.ProofClaim import ProofCategory, ProofScope

# exact active paths separate auxiliary evidence from unrelated assets and segments
KBrowserPrefix = "FusionAssetName[Active]/FusionBrowserSegmentType1/"

# the second independent pair can pass even when browser validation fails
KActPrefix = "FusionAssetName[Active]/FusionACTSegmentType1/"

# synthetic spans contain one primary and one inherited record with the same identity
KProofBulk = PackData("<I3sQ", 3, b"257", 42) + b"x" + PackData("<I3sQ", 3, b"256", 42)


# controlled native headers leave segment selection independent of record contents
def AuxMeta(
    Segment: SegmentKind,
    IndexValue: int,
    Storage: int,
    *,
    Version: int = 8,
    OtherOffset: int = 16,
) -> bytes:
    TextValue = Segment.value.encode("ascii")
    KindField = PackData("<I", len(TextValue)) + TextValue
    return b"".join(
        (
            KindField,
            PackData("<IIIIII", IndexValue, 0, 1234, Version, 0, 0),
            KindField,
            PackData("<IIII", 0, Storage, 0, 2),
            PackData("<I", 4),
            b"Base",
            PackData("<IIII", 0, 0, 0, 0),
            PackData("<I", 5),
            b"Child",
            PackData("<I", 4),
            b"Base",
            PackData("<IIIQ", 0, 0, 1, 42),
            PackData("<IIQQIQQQII", 0, 1, 42, 0, 1, 42, OtherOffset, 43, 0, 0),
        )
    )


# fake zip entries exercise canonical asset selection without copied vendor data
def AuxZip(Values: dict[str, bytes]) -> bytes:
    Buffer = BytesIO()
    with ZipFile(Buffer, "w") as Archive:
        for NameValue, DataValue in Values.items():
            Archive.writestr(NameValue, DataValue)
    return Buffer.getvalue()


# complete fixture pairs allow both members to be proven together
def AuxValues() -> dict[str, bytes]:
    return {
        KBrowserPrefix + "BulkStream.dat": KProofBulk,
        KBrowserPrefix + "MetaStream.dat": AuxMeta(SegmentKind.KBrowser, 2, 6),
        KActPrefix + "BulkStream.dat": KProofBulk,
        KActPrefix + "MetaStream.dat": AuxMeta(SegmentKind.KAct, 1, 5),
    }


# scoped claims are reproducible from the archive digest used by the proof caller
def AuxScope(DataValue: bytes) -> ProofScope:
    return ProofScope(ShaDigest(DataValue).hexdigest(), 35, 26)


# framing exposes exact ordered spans while preserving original design parser behavior
def TestAuxFrames() -> None:
    Values = AuxValues()
    DataValue = AuxZip(Values)
    Scope = AuxScope(DataValue)
    with OpenFusionZip(DataValue) as Archive:
        assert Archive.ReadNames == frozenset()
        Frame = ReadAuxFrame(Archive, SegmentKind.KBrowser)
        assert Frame.Spans == (
            RecordSpan(0, 15, 16, 42, 257, "Child", "", True),
            RecordSpan(16, 31, 31, 42, 256, "Base", "", False),
        )
        assert Archive.ReadNames == frozenset(
            (Frame.BulkMember.Name, Frame.MetaMember.Name)
        )
        Claims, Routes = ReadAuxProof(Archive, Scope)
        assert Routes is None
        assert tuple(
            CastValue(ArchiveMember, Value.Target).Name for Value in Claims
        ) == tuple(Values)
        assert all(
            Value.Scope == Scope and Value.Category is ProofCategory.KStructural
            for Value in Claims
        )
    BrowserMeta = Values[KBrowserPrefix + "MetaStream.dat"]
    with Raises(ValueError, match="design MetaStream"):
        _ = ReadBulkSpans(KProofBulk, BrowserMeta)


# wrong browser header fields and contradictory record extents leave the pair unresolved
def TestAuxHeader() -> None:
    KeyValue = KBrowserPrefix + "MetaStream.dat"
    for BadMeta in (
        AuxMeta(SegmentKind.KAct, 2, 6),
        AuxMeta(SegmentKind.KBrowser, 1, 6),
        AuxMeta(SegmentKind.KBrowser, 2, 5),
        AuxMeta(SegmentKind.KBrowser, 2, 6, Version=7),
        AuxMeta(SegmentKind.KBrowser, 2, 6, OtherOffset=0),
        AuxMeta(SegmentKind.KBrowser, 2, 6)[:-1],
    ):
        DataValue = AuxZip({**AuxValues(), KeyValue: BadMeta})
        with OpenFusionZip(DataValue) as Archive:
            Claims, _ = ReadAuxProof(Archive, AuxScope(DataValue))
            assert tuple(
                CastValue(ArchiveMember, Value.Target).Name for Value in Claims
            ) == (
                KActPrefix + "BulkStream.dat",
                KActPrefix + "MetaStream.dat",
            )


# moving a matching stream to another asset must leave the remaining member unread
def TestAuxForeign() -> None:
    Values = AuxValues()
    MetaName = KBrowserPrefix + "MetaStream.dat"
    Values[MetaName.replace("[Active]", "[Foreign]")] = Values.pop(MetaName)
    DataValue = AuxZip(Values)
    with OpenFusionZip(DataValue) as Archive:
        Claims, _ = ReadAuxProof(Archive, AuxScope(DataValue))
        assert len(Claims) == 2
        assert Archive.ReadNames == frozenset(
            (KActPrefix + "BulkStream.dat", KActPrefix + "MetaStream.dat")
        )


# local payload corruption can keep correct framing while violating central crc
def TestAuxCrc() -> None:
    DataValue = bytearray(AuxZip(AuxValues()))
    with ZipFile(BytesIO(DataValue)) as Archive:
        Header = Archive.getinfo(KActPrefix + "BulkStream.dat").header_offset
    NameSize, ExtraSize = UnpackFrom("<HH", DataValue, Header + 26)
    DataValue[Header + 30 + NameSize + ExtraSize + 15] ^= 1
    ArchiveData = bytes(DataValue)
    with OpenFusionZip(ArchiveData) as Archive:
        Claims, _ = ReadAuxProof(Archive, AuxScope(ArchiveData))
        assert tuple(
            CastValue(ArchiveMember, Value.Target).Name for Value in Claims
        ) == (
            KBrowserPrefix + "BulkStream.dat",
            KBrowserPrefix + "MetaStream.dat",
        )
