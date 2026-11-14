from typing import cast as CastValue

from convert.formats.Fusion.BundleCodec.Model.BundleFile import BundleFile
from convert.formats.Fusion.BundleCodec.Model.BundleGraph import BundleGraph
from convert.formats.Fusion.BundleCodec.Model.BundleLink import BundleLink
from convert.formats.Fusion.BundleCodec.Model.BundleModel import BundleModel
from convert.formats.Fusion.BundleCodec.Model.BundleObject import BundleObject
from convert.formats.Fusion.BundleCodec.Model.BundleRefs import BundleRefs
from convert.formats.Fusion.BundleCodec.Model.BundleText import BundleText
from convert.formats.Fusion.DrawingCodec.Author.Defaults.DrawingPolicy import (
    KBundleCreator,
    KDeflateMethod,
    KDesignType,
    KDrawingType,
    KFileUrn,
    KLineageUrn,
    KServiceName,
    KStorageUrn,
)
from convert.formats.Fusion.DrawingCodec.Author.Members.BuildManifests import (
    DesignUrl,
)
from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingSpec import DrawingSpec
from convert.formats.Fusion.DrawingCodec.Author.Model.SaveState import SaveState
from convert.formats.Fusion.DrawingCodec.Bundle.DrawingBundle import DrawingBundle
from convert.formats.Fusion.DrawingCodec.Bundle.ReadDrawBundle import (
    KDescriptionName,
    KManifestName,
)
from convert.formats.Fusion.DrawingCodec.Model.FusionDrawing import FusionDrawing
from convert.formats.Fusion.DrawingCodec.Model.PackageSlot import PackageSlot
from convert.formats.Fusion.DrawingCodec.Package.EntryLayout import EntryLayout
from convert.formats.Fusion.DrawingCodec.Package.PackageLimits import (
    KDescriptorFlag,
    KUtfFlag,
)

KDesignObject = 2

KDrawingObject = 1


def BuildBundle(
    SpecValue: DrawingSpec, Drawing: FusionDrawing, DesignData: bytes
) -> DrawingBundle:
    if not isinstance(CastValue(object, Drawing), FusionDrawing):
        raise ValueError("Expected a typed Fusion drawing")
    if type(DesignData) is not bytes or not DesignData:
        raise ValueError("Drawing bundles need the referenced design bytes")
    Identity = SpecValue.Identity
    History = SaveState() if SpecValue.History is None else SpecValue.History
    DesignPath = Identity.DesignFile + "." + KDesignType
    DrawingPath = Identity.DrawingFile + "." + KDrawingType
    Graph = BundleGraph(
        StampText(History.StampWords),
        KServiceName,
        (KDrawingObject,),
        (DesignEntry(SpecValue, DesignPath), DrawingEntry(SpecValue, DrawingPath)),
    )
    TimeWord, DateWord = History.StampWords
    Layout = EntryLayout(
        KDeflateMethod,
        KUtfFlag | KDescriptorFlag,
        TimeWord,
        DateWord,
        KBundleCreator,
        KBundleCreator,
        0,
    )
    return DrawingBundle(
        BundleModel("0", SpecValue.DrawingName, "1", Graph, DrawingPath),
        Drawing,
        (BundleFile(DesignPath, DesignData),),
        tuple(
            PackageSlot(NameValue, Layout)
            for NameValue in (KManifestName, KDescriptionName, DesignPath, DrawingPath)
        ),
    )


def DesignEntry(SpecValue: DrawingSpec, DesignPath: str) -> BundleObject:
    Design = SpecValue.Design
    return BundleObject(
        KDesignObject,
        Design.DesignVersion,
        DesignUrl(SpecValue),
        KLineageUrn + SpecValue.Identity.DesignToken,
        KStorageUrn + DesignPath,
        DesignPath,
        DesignPath,
        Design.DisplayName,
        Design.DisplayName + "." + KDesignType,
        "f3d",
        (),
        (),
        None,
    )


def DrawingEntry(SpecValue: DrawingSpec, DrawingPath: str) -> BundleObject:
    Token = SpecValue.Identity.DrawingToken
    Relation = BundleLink(
        KDesignObject,
        (
            BundleText("neutronRole", SpecValue.Identity.LinkRole),
            BundleText("neutronData", ""),
        ),
    )
    return BundleObject(
        KDrawingObject,
        1,
        KFileUrn + Token + "?version=1",
        KLineageUrn + Token,
        KStorageUrn + DrawingPath,
        DrawingPath,
        DrawingPath,
        SpecValue.DrawingName,
        SpecValue.DrawingName + "." + KDrawingType,
        "f2d",
        (BundleRefs("DERIVED", (KDesignObject,), (Relation,)),),
        (),
        None,
    )


def StampText(StampWords: tuple[int, int]) -> str:
    TimeWord, DateWord = StampWords
    DateText = (
        f"{(DateWord >> 9) + 1980:04d}-{DateWord >> 5 & 15:02d}-{DateWord & 31:02d}"
    )
    TimeText = (
        f"{TimeWord >> 11:02d}:{TimeWord >> 5 & 63:02d}:{(TimeWord & 31) * 2:02d}"
    )
    return DateText + "T" + TimeText + "+0000"
