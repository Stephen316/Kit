from dataclasses import fields as DataFields, is_dataclass as IsDataClass
from dataclasses import replace as Replace
from io import BytesIO
from math import cos as Cosine, isclose as IsClose, pi as KHalfTurn
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from typing import cast as CastValue
from zipfile import ZipFile

from pytest import mark as TestMark

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.formats.Fusion.SegmentCodec.Manifest.LinkLayout import (
    KLinkedAsset,
    KLinkedUrl,
)

KFixtures = (
    FilePath(__file__).resolve().parents[5]
    / "re"
    / "Fusion"
    / "LocalOracle"
    / "LinksConfigs"
    / "Fixtures"
)

KRequiresCodec = TestMark.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)

KReencoded = (".protein", ".smb", ".smbh")

KLinkCounts = (
    ("P_A1_saved", 0, ()),
    ("P_B1_saved", 0, ()),
    ("R0_empty", 0, ()),
    ("R1_part_a", 1, ("KitLinkPartA",)),
    ("R2_grounded", 1, ("KitLinkPartA",)),
    ("R3_nested", 2, ("KitLinkPartA", "KitLinkSub")),
    ("R4_joint", 2, ("KitLinkPartA", "KitLinkSub")),
    ("R5_saved", 2, ("KitLinkPartA", "KitLinkSub")),
    ("R6_out_of_date", 2, ("KitLinkPartA", "KitLinkSub")),
    ("R7_updated", 2, ("KitLinkPartA", "KitLinkSub")),
    ("R8_updated_saved", 2, ("KitLinkPartA", "KitLinkSub")),
    ("R9_archive", 2, ("KitLinkPartA", "KitLinkSub")),
    ("S0_inserted", 1, ("KitLinkPartB",)),
    ("S1_saved", 1, ("KitLinkPartB",)),
)

KControls = tuple(Entry[0] for Entry in KLinkCounts)

KNativeMatrix = (
    Cosine(KHalfTurn / 6),
    -0.5,
    0.0,
    5.0,
    0.5,
    Cosine(KHalfTurn / 6),
    0.0,
    2.0,
    0.0,
    0.0,
    1.0,
    1.0,
    0.0,
    0.0,
    0.0,
    1.0,
)

KMovedMatrix = (
    Cosine(KHalfTurn / 4),
    -Cosine(KHalfTurn / 4),
    0.0,
    7.0,
    Cosine(KHalfTurn / 4),
    Cosine(KHalfTurn / 4),
    0.0,
    -3.0,
    0.0,
    0.0,
    1.0,
    2.0,
    0.0,
    0.0,
    0.0,
    1.0,
)


def ReadMembers(DataValue: bytes) -> dict[str, bytes]:
    with ZipFile(BytesIO(DataValue)) as Archive:
        return {Entry: Archive.read(Entry) for Entry in Archive.namelist()}


def CollectMut(Value: object, Found: list[CrossRef]) -> list[CrossRef]:
    if isinstance(Value, CrossRef):
        Found.append(Value)
    elif isinstance(Value, tuple):
        for Entry in CastValue(tuple[object, ...], Value):
            _ = CollectMut(Entry, Found)
    elif IsDataClass(Value) and not isinstance(Value, type):
        for FieldInfo in DataFields(Value):
            _ = CollectMut(getattr(Value, FieldInfo.name), Found)
    return Found


def IsSameMatrix(Value: MatrixValue, Target: tuple[float, ...]) -> bool:
    return Value.Entries is not None and all(
        IsClose(LeftValue, RightValue, abs_tol=1e-9)
        for LeftValue, RightValue in zip(Value.Entries, Target, strict=True)
    )


def MoveMatrix(Value: object) -> object:
    if isinstance(Value, MatrixValue):
        return (
            MatrixValue(KMovedMatrix) if IsSameMatrix(Value, KNativeMatrix) else Value
        )
    if isinstance(Value, tuple):
        return tuple(
            MoveMatrix(Entry) for Entry in CastValue(tuple[object, ...], Value)
        )
    if IsDataClass(Value) and not isinstance(Value, type):
        return Replace(
            Value,
            **{
                FieldInfo.name: MoveMatrix(getattr(Value, FieldInfo.name))
                for FieldInfo in DataFields(Value)
                if FieldInfo.init
            },
        )
    return Value


def CountMatrix(Value: object, Target: tuple[float, ...]) -> int:
    if isinstance(Value, MatrixValue):
        return int(IsSameMatrix(Value, Target))
    if isinstance(Value, tuple):
        return sum(
            CountMatrix(Entry, Target) for Entry in CastValue(tuple[object, ...], Value)
        )
    if IsDataClass(Value) and not isinstance(Value, type):
        return sum(
            CountMatrix(getattr(Value, FieldInfo.name), Target)
            for FieldInfo in DataFields(Value)
        )
    return 0


def LoadFixture(StemName: str) -> bytes:
    return (KFixtures / f"{StemName}.f3d").read_bytes()


@KRequiresCodec
@TestMark.parametrize("StemName", KControls)
def TestLinkReplay(StemName: str) -> None:
    Source = LoadFixture(StemName)
    Model = ReadDocument(Source)
    Output = EmitParsed(Model)
    assert ReadDocument(Output) == Model
    Before, After = ReadMembers(Source), ReadMembers(Output)
    assert set(Before) == set(After)
    Changed = {
        Entry
        for Entry in Before
        if Before[Entry] != After[Entry] and not Entry.endswith(KReencoded)
    }
    assert not Changed


@KRequiresCodec
@TestMark.parametrize("StemName,LinkCount,Targets", KLinkCounts)
def TestLinkTables(StemName: str, LinkCount: int, Targets: tuple[str, ...]) -> None:
    Model = ReadDocument(LoadFixture(StemName))
    RootLinks = Model.Document.Links
    assert len(RootLinks) == len(Model.Asset.Links) == LinkCount
    assert (
        tuple(sorted(dict(Entry.Properties)["toDocDisplayName"] for Entry in RootLinks))
        == Targets
    )
    Assets = {Entry.LinkId: Entry.AssetId for Entry in Model.Asset.Links}
    for Entry in RootLinks:
        Fields = dict(Entry.Properties)
        assert Fields[KLinkedAsset] == Assets[Entry.LinkId]
        assert Fields[KLinkedUrl].startswith("urn:adsk.wipprod:fs.file:vf.")
    for Segment in Model.Segments:
        Contexts = Segment.Metadata.Contexts
        assert len(Contexts) == LinkCount
        assert {Entry.LinkId for Entry in Contexts} == set(Assets)
        Tokens = {Entry.Token for Entry in Contexts}
        Crossing = CollectMut(Segment.Records, [])
        assert bool(Crossing) == bool(LinkCount)
        assert all(Entry.Token in Tokens for Entry in Crossing)


@KRequiresCodec
def TestLinkUpdate() -> None:
    Stale = ReadDocument(LoadFixture("R6_out_of_date"))
    Fresh = ReadDocument(LoadFixture("R7_updated"))
    StaleIds = {Entry.LinkId for Entry in Stale.Document.Links}
    FreshIds = {Entry.LinkId for Entry in Fresh.Document.Links}
    assert len(StaleIds - FreshIds) == len(FreshIds - StaleIds) == 1
    LinkUrls = {
        dict(Entry.Properties)["toDocDisplayName"]: dict(Entry.Properties)[KLinkedUrl]
        for Entry in Fresh.Document.Links
    }
    assert LinkUrls["KitLinkPartA"].endswith("?version=2")
    assert LinkUrls["KitLinkSub"].endswith("?version=1")


@KRequiresCodec
def TestLinkTokens() -> None:
    Model = ReadDocument(LoadFixture("R3_nested"))
    Tokens = {
        Segment.Metadata.Header.Segment.name: {
            Entry.LinkId: (Entry.Token, Entry.SegmentId)
            for Entry in Segment.Metadata.Contexts
        }
        for Segment in Model.Segments
    }
    assert Tokens["KDesign"] == Tokens["KBrowser"]
    assert all(SegmentId == 0 for _, SegmentId in Tokens["KDesign"].values())
    assert all(SegmentId == 1 for _, SegmentId in Tokens["KAct"].values())
    assert all(
        Tokens["KAct"][LinkId][0] != Token
        for LinkId, (Token, _) in Tokens["KDesign"].items()
    )


@KRequiresCodec
def TestPlacement() -> None:
    Model = ReadDocument(LoadFixture("R1_part_a"))
    assert CountMatrix(Model.Segments, KNativeMatrix) == 4
    Edited = MoveMatrix(Model)
    assert isinstance(Edited, type(Model))
    Again = ReadDocument(EmitParsed(Edited))
    assert Again == Edited
    assert CountMatrix(Again.Segments, KMovedMatrix) == 4
    assert CountMatrix(Again.Segments, KNativeMatrix) == 0
    assert Again.Graphics == Model.Graphics
