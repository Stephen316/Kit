"""Replay the witnessed P04 presentation suffix on the shared Config-0 map."""

from argparse import ArgumentParser
from hashlib import sha256 as Sha256
import json as Json
from pathlib import Path
from struct import unpack_from as UnpackFrom
from sys import path as ImportPaths
from sys import stdout as StandardOutput

from SketchEvidence import (
    KApplicationBuild,
    KCaptureRev,
    KReceiptDigest,
    ReadPinned,
    ReadReceipts,
)

if __name__ == "__main__":
    ImportPaths.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from SketchReader import ReadSketchConfiguration
from SketchRoot import Require
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KNullKind,
    KObjectRefKind,
)
from convert.adapters.solidworks.container.Container import SldprtArchive


# fixed presentation spans come from successive typed calls in the P04 map witness
def ReadPointers(Cursor, Events, Steps):
    for Width, KindValue, NameValue in Steps:
        Cursor.AdvanceBytes(Width)
        ReadPointer(Cursor, Events, KindValue, NameValue)


# capture the order and counter that native ReadObject observes before each token
def ReadPointer(Cursor, Events, KindValue, NameValue=None, SchemaValue=1):
    Offset, Counter = Cursor.Offset, Cursor.NextIndex
    TagValue, _, Index = Cursor.TakePointer((NameValue,), KindValue, SchemaValue)
    Events.append((Offset, Counter, TagValue.kind, NameValue, Index))


# the presence byte selects the nine-double matrix before the translation and scale
def ReadViewXform(Cursor):
    (MatrixFlag,) = Cursor.ReadValue("<B")
    Require(MatrixFlag in (0, 1), True, "view transform matrix flag")
    if MatrixFlag:
        Cursor.ReadPoint(9)
    Cursor.ReadPoint(4)
    Require(Cursor.ReadValue("<B"), (0,), "view transform extension mode")


# the three optional view collections have no entries on the witnessed path
def ReadConfigView(Cursor):
    Cursor.ReadText()
    for _ in range(2):
        ReadViewXform(Cursor)
    Cursor.ReadValue("<Hi")
    Cursor.ReadPoint(1)
    Require(Cursor.ReadCount(), 0, "empty view pointer array")
    Cursor.ReadValue("<2i")
    Require(Cursor.ReadCount(), 0, "empty first view list")
    Cursor.ReadValue("<i")
    Cursor.ReadPoint(1)
    Require(Cursor.ReadCount(), 0, "empty second view list")
    Cursor.ReadValue("<2i")


# dimension styles store the scalar unit base and a length code before their child
def ReadLengthUnit(Cursor, Events):
    Cursor.ReadValue("<2i")
    Cursor.ReadPoint(1)
    Cursor.ReadValue("<2i")
    Cursor.ReadPoint(1)
    Cursor.ReadValue("<4i")
    Cursor.ReadPoint(1)
    _, _, UnitCode = Cursor.ReadValue("<HiH")
    Require(UnitCode <= 10, True, "length unit code")
    ReadPointer(Cursor, Events, KNullKind)


# standard annotation views use the same transform serializer as regular views
def ReadAnnotationView(Cursor, Events, NameValues):
    Require(Cursor.ReadText() in NameValues, True, "witnessed annotation view name")
    for _ in range(2):
        ReadViewXform(Cursor)
    ReadPointers(
        Cursor,
        Events,
        (
            (58, KNullKind, None),
            (0, KNullKind, None),
            (12, KNullKind, None),
            (8, KNullKind, None),
        ),
    )


# each inline region carries a count and scalar rows without allocating archive objects
def ReadModelRegions(Cursor):
    Require(Cursor.ReadCount(), 0, "empty modern model text-pair table")
    Cursor.AdvanceBytes(13)
    Count = Cursor.ReadCount()
    Require(Count in (0, 1, 2), True, "witnessed model region groups")
    Regions = []
    for _ in range(Count):
        ItemCount = Cursor.ReadCount()
        Require(ItemCount in (0, 1), True, "witnessed model region group size")
        Items = []
        for _ in range(ItemCount):
            BodyId, RegionId = Cursor.ReadValue("<2i")
            (Scalar,) = Cursor.ReadPoint(1)
            Items.append((BodyId, RegionId, Scalar))
        Regions.append(Items)
    if Count == 2:
        Cursor.ReadValue("<i")
    Cursor.AdvanceBytes(258 if Count else 4)
    return Regions


# this research continuation is bounded to the pinned build and witnessed suffix layout
def ReadConfigMap(BlobValue, BuildName):
    Require(BuildName, KApplicationBuild, "witnessed P04 model build")
    _, Cursor = ReadSketchConfiguration(BlobValue, BuildName)
    Start = (Cursor.Offset, Cursor.NextIndex)
    Events, Regions = ReadModelPresentation(Cursor)
    return Cursor, {"start": Start, "regions": Regions, "pointers": Events}


# the same model serializer stores the presentation records after either relation path
def ReadModelPresentation(Cursor):
    Events = []
    Cursor.AdvanceBytes(1183)
    ReadPointer(Cursor, Events, KClassRefKind, "moLengthUserUnits_c")
    ReadLengthUnit(Cursor, Events)
    Cursor.AdvanceBytes(442)
    ReadPointer(Cursor, Events, KNullKind)
    for Width in (434, 430, 438, 434, 446, 470, 438, 450):
        Cursor.AdvanceBytes(Width)
        ReadPointer(Cursor, Events, KClassRefKind, "moLengthUserUnits_c")
        ReadLengthUnit(Cursor, Events)
    ReadPointers(
        Cursor,
        Events,
        (
            (9053, KNullKind, None),
            (0, KNullKind, None),
            (48, KNullKind, None),
            (0, KNullKind, None),
            (2680, KDefinitionKind, "moEnvFolder_c"),
            (0, KClassRefKind, "moNodeName_c"),
            (64, KNullKind, None),
            (2, KDefinitionKind, "moAmbientLight_c"),
            (0, KClassRefKind, "moNodeName_c"),
            (42, KNullKind, None),
            (47, KNullKind, None),
            (30, KNullKind, None),
        ),
    )
    for Width, KindValue in (
        (142, KDefinitionKind),
        (182, KClassRefKind),
        (182, KClassRefKind),
    ):
        ReadPointers(
            Cursor,
            Events,
            (
                (Width, KindValue, "moDirectionLight_c"),
                (0, KClassRefKind, "moNodeName_c"),
                (52, KNullKind, None),
                (47, KNullKind, None),
                (30, KNullKind, None),
            ),
        )
    ReadPointers(Cursor, Events, ((227, KNullKind, None), (30, KNullKind, None), (44, KNullKind, None)))
    ListKind = KClassRefKind if "suObList" in Cursor.Classes.values() else KDefinitionKind
    ReadPointer(Cursor, Events, ListKind, "suObList")
    Require(Cursor.ReadValue("<H"), (0,), "empty leading view list")
    ReadPointer(Cursor, Events, KDefinitionKind, "moView_c")
    ReadConfigView(Cursor)
    for _ in range(9):
        ReadPointer(Cursor, Events, KClassRefKind, "moView_c")
        ReadConfigView(Cursor)
    Cursor.AdvanceBytes(9)
    ReadPointer(Cursor, Events, KDefinitionKind, "moFeatColorTab_c", 0)
    ReadPointers(
        Cursor,
        Events,
        (
            (4, KNullKind, None),
            (12, KDefinitionKind, "moSketchBlockMgr_c"),
            (0, KNullKind, None),
            (24, KNullKind, None),
            (47, KNullKind, None),
            (30, KNullKind, None),
            (56, KObjectRefKind, "moSketchBlockMgr_c"),
            (8, KClassRefKind, "suObList"),
        ),
    )
    (AnnotationCount,) = Cursor.ReadValue("<H")
    Require(AnnotationCount in (1, 2), True, "witnessed annotation view count")
    ReadPointer(Cursor, Events, KDefinitionKind, "moAnnotationView_c")
    ReadAnnotationView(Cursor, Events, ("*Front", "*Right"))
    if AnnotationCount == 2:
        ReadPointers(Cursor, Events, ((16, KClassRefKind, "moAnnotationView_c"),))
        ReadAnnotationView(Cursor, Events, ("*Top",))
    ReadPointers(
        Cursor,
        Events,
        (
            (32, KNullKind, None),
            (24, KNullKind, None),
            (2, KDefinitionKind, "moPMarkRecord_c"),
            (48, KClassRefKind, "suObList"),
            (14, KDefinitionKind, "moCThreadRefMgr_c"),
            (8, KNullKind, None),
        ),
    )
    Regions = ReadModelRegions(Cursor)
    ReadPointers(
        Cursor,
        Events,
        (
            (0, KDefinitionKind, "moPrtExplViewManager_c"),
            (0, KNullKind, None),
            (24, KNullKind, None),
            (47, KNullKind, None),
            (30, KNullKind, None),
            (36, KNullKind, None),
            (0, KNullKind, None),
        ),
    )
    Cursor.AdvanceBytes(54)
    Require(Cursor.Offset, len(Cursor.BlobValue), "complete witnessed Config-0 extent")
    return Events, Regions


# the saved header can corroborate the derived map but never initializes it
def ReportConfigurationMaps(RootPath):
    Receipt, _ = ReadReceipts(RootPath)
    Results = []
    for Capture in Receipt["native_files"]:
        NameValue = Capture["file"]
        Data = ReadPinned(RootPath, NameValue)
        Require(Sha256(Data).hexdigest(), Capture["sha256"], "pinned Config-0 part")
        Archive = SldprtArchive.from_bytes(Data, NameValue)
        Config = Archive.require("Contents/Config-0")
        Resolved = Archive.require("Contents/Config-0-ResolvedFeatures")
        Cursor, Walk = ReadConfigMap(Config, KApplicationBuild)
        (Header,) = UnpackFrom("<I", Resolved)
        Require(Cursor.NextIndex, Header, "derived map and P04 resolved header")
        Results.append(
            {
                "capture": NameValue,
                "sha256": Sha256(Config).hexdigest(),
                "end": Cursor.Offset,
                "next_map_index": Cursor.NextIndex,
                "sketch_objects": [
                    Slot for Slot, Name in Cursor.Objects.items() if Name == "sgSketch"
                ],
                **Walk,
            }
        )
    return {
        "scope": "p04_discovery_config_map",
        "capture_revision": KCaptureRev,
        "capture_receipt_sha256": KReceiptDigest,
        "application_build": KApplicationBuild,
        "captures": Results,
    }


if __name__ == "__main__":
    Parser = ArgumentParser(description=__doc__)
    Parser.parse_args()
    RootPath = Path(__file__).resolve().parents[3]
    Evidence = ReportConfigurationMaps(RootPath)
    Text = Json.dumps(Evidence, sort_keys=True, indent=2, allow_nan=False)
    StandardOutput.buffer.write((Text + "\n").encode("utf-8"))
