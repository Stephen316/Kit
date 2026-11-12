from dataclasses import replace as Replace
from pathlib import Path as FilePath
from struct import pack as PackValue
from sys import version_info as PythonVersion

from pytest import mark as TestMark, raises as Raises

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Browser.BrowserLayout import KMaxRootLength
from convert.formats.Fusion.SegmentCodec.Browser.BrowserRoot import (
    BrowserFolder,
    BrowserGroup,
    BrowserRoot,
    BrowserRoute,
)
from convert.formats.Fusion.SegmentCodec.Browser.EmitBrowserRoot import (
    EmitBrowserRoot,
)
from convert.formats.Fusion.SegmentCodec.Browser.ReadBrowserRoot import (
    ReadBrowserRoot,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ReadAuxFrame import ReadAuxFrame

# the two controls cover both native group orders and the alternate route flag
KRepoRoot = FilePath(__file__).resolve().parents[4]

# native archive fixtures use the standard library codec from the newer runtime
KRequiresCodec = TestMark.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)

# typed synthetic data exercises zero identity and preserves the composite route key
KSyntheticRoot = BrowserRoot(
    0,
    (BrowserRoute(0, 1, 5), BrowserRoute(0, 0, 2)),
    8,
    (
        BrowserGroup(
            4,
            (
                BrowserFolder("Names", 17),
                BrowserFolder("More", 13),
                BrowserFolder("Rest", 22),
                BrowserFolder("Other", 11),
                BrowserFolder("Last", 19),
            ),
        ),
        BrowserGroup(None, (BrowserFolder("Single", 27),)),
    ),
)


# native scalar packing in the expected bytes independently fixes each reference lane
def FolderFixture(Label: bytes, Identity: int) -> bytes:
    return PackValue("<I", len(Label)) + Label + PackValue("<BQH", 1, Identity, 0)


# fixed vectors check framing without feeding captured native payloads into production
def TestSynthetic() -> None:
    Expected = (
        PackValue("<I20s2xBQH4xBI", 20, b"PersistBrowserRootId", 1, 0, 256, 1, 2)
        + PackValue("<BQHIBQH", 1, 0, 256, 1, 1, 5, 0)
        + PackValue("<BQHIBQH", 1, 0, 256, 0, 1, 2, 0)
        + PackValue("<BQHIBQHII", 1, 8, 0, 2, 1, 4, 256, 0, 5)
        + FolderFixture(b"Names", 17)
        + FolderFixture(b"More", 13)
        + FolderFixture(b"Rest", 22)
        + FolderFixture(b"Other", 11)
        + FolderFixture(b"Last", 19)
        + PackValue("<BI", 0, 1)
        + FolderFixture(b"Single", 27)
    )
    assert EmitBrowserRoot(KSyntheticRoot) == Expected
    assert ReadBrowserRoot(Expected) == KSyntheticRoot


# malformed counts lanes and duplicate keys cannot masquerade as valid records
@TestMark.parametrize(
    ("Offset", "Replacement"),
    (
        (24, b"\x01"),
        (35, b"\x01"),
        (42, PackValue("<I", 129)),
        (57, PackValue("<I", 2)),
        (70, b"\x01"),
        (83, PackValue("<I", 1)),
        (109, PackValue("<I", 3)),
        (124, PackValue("<I", 1)),
        (128, PackValue("<I", 6)),
        (136, b"\n"),
    ),
)
def TestWireRejects(Offset: int, Replacement: bytes) -> None:
    Payload = EmitBrowserRoot(KSyntheticRoot)
    Changed = Payload[:Offset] + Replacement + Payload[Offset + len(Replacement) :]
    assert Changed != Payload
    with Raises(ValueError):
        _ = ReadBrowserRoot(Changed)


# every nested field must be present and extra bytes stay outside the supported root
def TestWireExtent() -> None:
    Payload = EmitBrowserRoot(KSyntheticRoot)
    for Length in range(len(Payload)):
        with Raises(ValueError):
            _ = ReadBrowserRoot(Payload[:Length])
    with Raises(ValueError, match="trailing data"):
        _ = ReadBrowserRoot(Payload + b"\x00")
    with Raises(ValueError, match="payload size"):
        _ = ReadBrowserRoot(bytes(KMaxRootLength + 1))


# programmatic writes reject malformed identities and unbounded text before packing
def TestBadModel() -> None:
    Group = KSyntheticRoot.Groups[0]
    for RootValue in (
        Replace(KSyntheticRoot, DesignRootId=-1),
        Replace(KSyntheticRoot, BrowserRootId=1 << 64),
        Replace(KSyntheticRoot, Routes=(BrowserRoute(0, True, 2),)),
        Replace(KSyntheticRoot, Routes=(BrowserRoute(0, 0, 2),) * 2),
        Replace(KSyntheticRoot, Groups=(Group, Group)),
        Replace(
            KSyntheticRoot,
            Groups=(Replace(Group, ScopeId=True), *KSyntheticRoot.Groups[1:]),
        ),
        Replace(
            KSyntheticRoot,
            Groups=(Group, BrowserGroup(None, (BrowserFolder("é", 1),))),
        ),
    ):
        with Raises(ValueError):
            _ = EmitBrowserRoot(RootValue)


# representative saved roots preserve both serialized orders and the alternate key
@KRequiresCodec
@TestMark.parametrize(
    ("RelativeName", "FolderCounts", "Flags"),
    (
        ("re/Fusion/Study/planedefinitions-6cd0820a832e/offset.f3d", (1, 5), {0}),
        ("examples/.f3d/example2.f3d", (5, 1), {0, 1}),
    ),
)
def TestSavedReplay(
    RelativeName: str, FolderCounts: tuple[int, int], Flags: set[int]
) -> None:
    with OpenFusionZip((KRepoRoot / RelativeName).read_bytes()) as Archive:
        Frame = ReadAuxFrame(Archive, SegmentKind.KBrowser)
        (SpanValue,) = tuple(
            NativeSpan
            for NativeSpan in Frame.Spans
            if NativeSpan.IsPrimary
            and NativeSpan.ObjectId == 0
            and NativeSpan.ClassGuid == "33F72249-4935-47EB-8282-B2C3D93546CE"
        )
    Payload = Frame.BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset]
    RootValue = ReadBrowserRoot(Payload)
    assert tuple(len(Group.Folders) for Group in RootValue.Groups) == FolderCounts
    assert {Route.RouteFlag for Route in RootValue.Routes} == Flags
    assert EmitBrowserRoot(RootValue) == Payload
