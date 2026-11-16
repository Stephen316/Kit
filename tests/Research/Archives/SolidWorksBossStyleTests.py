from hashlib import sha256 as Sha256
from importlib.util import (
    module_from_spec as LoadModule,
    spec_from_file_location as LoadSpec,
)
from json import loads as LoadJson
from pathlib import Path as FilePath
from struct import pack as PackFields
from typing import Protocol, TypedDict, cast as CastValue

import pytest as Pytest

from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    ArchiveError,
    ContainerMo,
)
from convert.adapters.solidworks.container.ArchiveCursor import (
    ArchiveCursor,
    FieldCursor,
)
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.resolved.RectanglePart import ReadRectPart
from convert.adapters.solidworks.sketch.DisplayOpen import (
    ReadDisplayBase,
    ReadDisplayOpen,
)

# the repository root anchors both pinned native data and unpackaged research code
KRepoRoot = FilePath(__file__).resolve().parents[3]

# the receipt and its measured observations bind each saved file to the corpus
KCaptureDir = KRepoRoot / "re/automation/PairedCaptures/P03/solidworks-db1390476325"

# the immutable receipt commits the exact byte identity of each archive
KReceiptHash = "f2308ae749f3d739746301873a49e997e2cf494f9d459e954403b66b17e22a94"

# the independent walkthrough recorded a style boundary for every pinned save
KStyleCases = (
    ("baseline-a", 13273),
    ("baseline-b", 13501),
    ("edit-width_mm-41", 13501),
    ("edit-height_mm-23", 13501),
    ("edit-depth_mm-12", 13501),
    ("units-inch", 13501),
    ("plane-yz", 13343),
    ("direction-negative", 13271),
)


# the frozen native output identifies the exact archive and records save diagnostics
class SavedPart(TypedDict):
    file: str
    sha256: str
    size_bytes: int
    save_errors: int
    save_warnings: int


# a pinned save receipt also binds the independent native measurements
class SaveReceipt(TypedDict):
    recipe_id: str
    errors: int
    measurements: str
    measurement_receipt_sha256: str
    native_files: list[SavedPart]


# the hosted boundary loads the research codec by file without packaging it
class BossStyleCodec(Protocol):

    # generation and display controls are explicit inputs to the native field encoder
    def EncodeBlindBossDisplayStyle(
        self, *, Generation: int, DisplayMode: int, ConditionOne: bool
    ) -> bytes: ...

    # the reader exposes its next offset so the archive caller can resume
    def ReadBlindBossDisplayStyle(
        self,
        BlobValue: bytes,
        Offset: int,
        *,
        Generation: int,
        DisplayMode: int,
        ConditionOne: bool,
    ) -> int: ...


# an exact path keeps the research module independent of import search ordering
def LoadBossStyleCodec() -> BossStyleCodec:
    SpecValue = LoadSpec(
        "solidworks_boss_display_style",
        KRepoRoot / "re/solidworks/WriterResearch/DisplayStyle.py",
    )
    assert SpecValue is not None and SpecValue.loader is not None
    ModuleValue = LoadModule(SpecValue)
    SpecValue.loader.exec_module(ModuleValue)
    return CastValue(BossStyleCodec, ModuleValue)


# only exact files from the independent eight save receipt can witness shape
def ReadPinnedBossPart(Variant: str) -> SldprtArchive:
    ReceiptBytes = (KCaptureDir / "receipt.json").read_bytes()
    assert Sha256(ReceiptBytes).hexdigest() == KReceiptHash
    Receipt = CastValue(SaveReceipt, LoadJson(ReceiptBytes))
    assert (Receipt["recipe_id"], Receipt["errors"], Receipt["measurements"]) == (
        "P03",
        0,
        "measurements.json",
    )
    MeasurementBytes = (KCaptureDir / Receipt["measurements"]).read_bytes()
    assert Sha256(MeasurementBytes).hexdigest() == Receipt["measurement_receipt_sha256"]
    assert tuple(Part["file"] for Part in Receipt["native_files"]) == tuple(
        f"P03-solidworks-{Case}.SLDPRT" for Case, _ in KStyleCases
    )
    (Part,) = tuple(
        Saved
        for Saved in Receipt["native_files"]
        if Saved["file"] == f"P03-solidworks-{Variant}.SLDPRT"
    )
    assert (Part["save_errors"], Part["save_warnings"]) == (0, 0)
    RawPart = (KCaptureDir / Part["file"]).read_bytes()
    assert (len(RawPart), Sha256(RawPart).hexdigest()) == (
        Part["size_bytes"],
        Part["sha256"],
    )
    return SldprtArchive.from_bytes(RawPart)


# the normal boss reader proves ownership before the null opening reaches the style
def ReadBossStyleBoundary(Variant: str) -> tuple[bytes, int, int]:
    Archive = ReadPinnedBossPart(Variant)
    Generation = ContainerMo(Archive.streams)
    assert Generation == 19000
    Resolved = Archive.require("Contents/Config-0-ResolvedFeatures")
    Parsed = ReadRectPart(Archive.require("Contents/Config-0"), Resolved, Generation)
    assert Parsed.Boss is not None
    EndSpec = Parsed.Boss["end_specification"]
    Depth = Parsed.Boss["depth_display"]
    assert EndSpec["conditions"] == (0, 0)
    assert EndSpec["depth_dimension_offset"] == Depth["offset"]
    ClassName = "moDisplayDistanceDim_c"
    Cursor = ArchiveCursor(
        Resolved,
        Depth["offset"],
        Depth["object_index"],
        {EndSpec["depth_dimension_class"]: ClassName},
        {},
    )
    _, _, DisplayObject = Cursor.TakePointer(
        (ClassName,), KClassRefKind, CompactOnly=True
    )
    assert DisplayObject == Depth["object_index"]
    Opening = Cursor.Offset
    ReadDisplayBase(Cursor, False, DisplayMode=201)
    Cursor.ReadNull()
    StyleOffset = Cursor.Offset
    Cursor.Offset = Opening
    ReadDisplayOpen(Cursor, DisplayMode=201)
    assert Cursor.Offset == Depth["handle"]["offset"]
    assert Cursor.Objects == {DisplayObject: ClassName}
    assert Cursor.NextIndex == DisplayObject + 1
    return Resolved, StyleOffset, Generation


# the generated fragment must end at the adjacent native positions and directions
@Pytest.mark.parametrize(("Variant", "NativeStyleOffset"), KStyleCases)
def CheckBlindBossStyle(Variant: str, NativeStyleOffset: int) -> None:
    Resolved, StyleOffset, Generation = ReadBossStyleBoundary(Variant)
    assert StyleOffset == NativeStyleOffset
    Codec = LoadBossStyleCodec()
    Emitted = Codec.EncodeBlindBossDisplayStyle(
        Generation=Generation, DisplayMode=201, ConditionOne=False
    )
    After = Codec.ReadBlindBossDisplayStyle(
        Resolved,
        StyleOffset,
        Generation=Generation,
        DisplayMode=201,
        ConditionOne=False,
    )
    assert After - StyleOffset == len(Emitted) == 94
    assert Emitted == Resolved[StyleOffset:After]
    Positions = FieldCursor(Resolved, After)
    assert Positions.ReadPoint(12) == (0.0,) * 12
    assert Positions.ReadInts("<i") == (2,)
    _ = Positions.ReadPoint(6)
    assert Positions.ReadText() == ""
    assert Positions.ReadPoint(3) == (0.0,) * 3
    assert Positions.ReadInts("<i") == (18,)


# a nonempty map count at the witnessed boundary cannot reuse the empty default layout
def CheckBlindBossStyleMapGuard() -> None:
    Resolved, StyleOffset, Generation = ReadBossStyleBoundary("baseline-a")
    MapOffset = StyleOffset + 8
    assert Resolved[MapOffset : MapOffset + 4] == PackFields("<i", 0)
    Altered = Resolved[:MapOffset] + PackFields("<i", 1) + Resolved[MapOffset + 4 :]
    Codec = LoadBossStyleCodec()
    with Pytest.raises(ArchiveError, match="normal blind boss display style"):
        _ = Codec.ReadBlindBossDisplayStyle(
            Altered,
            StyleOffset,
            Generation=Generation,
            DisplayMode=201,
            ConditionOne=False,
        )
