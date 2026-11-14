from uuid import UUID

from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    HandleNumber,
    HardOwner,
    SoftPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import KDraftValue
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import (
    KDraftFields,
    PlaceMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceFolder import (
    EnrolMut,
    PlaceFolderMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceRecord import (
    PlaceRecordMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import (
    KFusionSource,
    KRootFolder,
    KSourceManager,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewSource import ViewSource
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.HoleData import HoleData

KRoundTrip = "ACAD_XREC_ROUNDTRIP"
KIdentity = (
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
)


def GuidGroups(GuidText: str) -> tuple[tuple[str, KDraftValue], ...]:
    try:
        Parts = UUID(GuidText).fields
    except ValueError as Failure:
        raise ValueError(
            f"Authored DWG body GUID {GuidText!r} is malformed"
        ) from Failure
    Trailing = UUID(GuidText).bytes[8:]
    Words = (Parts[0], Parts[1], Parts[2], *Trailing)
    return tuple(
        ("90", Datum - (1 << 32) if Datum >= 1 << 31 else Datum) for Datum in Words
    )


def SourceGroups(Source: ViewSource) -> tuple[tuple[str, KDraftValue], ...]:
    BodyText = f"{Source.BodyId:X}"
    return (
        ("102", "ACAD_ROUNDTRIP_2014_VIEWREP_FUSIONSRC"),
        ("1", Source.ComponentText),
        *(("90", Datum) for Datum in (1, 1, 0, 0, 1, 1)),
        ("5", BodyText),
        *(("90", 0) for _ in range(3)),
        *(("40", Value) for Value in KIdentity),
        ("90", 1),
        ("90", 1),
        ("5", BodyText),
        *GuidGroups(Source.GeometryGuid),
        ("1", Source.MaterialText),
    )


def PlaceSourceMut(Ledger: DraftBook, Source: ViewSource) -> None:
    Owner: KDraftFields = {
        "Owner": SoftPointer(KRootFolder),
        "Reactors": (SoftPointer(KRootFolder),),
    }
    Mappings = KRootFolder + "/SY_MAPPINGS"
    _ = EnrolMut(Ledger, KRootFolder, "SY_MAPPINGS", Mappings)
    _ = PlaceMut(Ledger, Mappings, "ACDBSYNERGYMAPPINGS", Owner, {})
    Holes = KRootFolder + "/SY_REFERENCEDATAHOLE_DATA"
    _ = EnrolMut(Ledger, KRootFolder, "SY_REFERENCEDATAHOLE_DATA", Holes)
    _ = PlaceMut(
        Ledger,
        Holes,
        "ACDBREFERENCEDATA",
        Owner,
        {
            "TextTwo": Source.ComponentText,
            "TextThree": Source.ComponentText,
            "TextFour": HoleData(Source.BodyId),
        },
    )
    _ = EnrolMut(Ledger, KRootFolder, "SY_VIEWSOURCEMGR", KSourceManager)
    Folder = KSourceManager + "/Xdic"
    _ = PlaceMut(
        Ledger,
        KSourceManager,
        "ACDBVIEWREPSOURCEMGR",
        {
            **Owner,
            "ReactorCount": 1,
            "NoXdic": 0,
            "HasDsData": 0,
            "Xdic": HardOwner(Folder),
        },
        {"SourceFlag": 0, "SourceLong": 0},
    )
    Record = PlaceFolderMut(Ledger, Folder, KSourceManager, True, KRoundTrip)
    _ = PlaceRecordMut(
        Ledger,
        Record,
        Folder,
        (
            ("102", "ACAD_ROUNDTRIP_2016_VIEWREP_SOURCEMGR"),
            ("90", 1),
            ("350", HandleNumber(KFusionSource)),
        ),
    )
    PlaceFusionMut(Ledger, Source, Record)


def PlaceFusionMut(Ledger: DraftBook, Source: ViewSource, RecordKey: str) -> None:
    Folder = KFusionSource + "/Xdic"
    _ = PlaceMut(
        Ledger,
        KFusionSource,
        "ACDBVIEWREPFUSIONSOURCE",
        {"Owner": SoftPointer(RecordKey), "Xdic": HardOwner(Folder)},
        {},
    )
    Record = PlaceFolderMut(Ledger, Folder, KFusionSource, True, KRoundTrip)
    _ = PlaceRecordMut(Ledger, Record, Folder, SourceGroups(Source))
