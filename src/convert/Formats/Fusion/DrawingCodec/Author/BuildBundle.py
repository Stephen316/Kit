from typing import cast as CastValue

from convert.Formats.Fusion.BundleCodec.Model.BundleFile import BundleFile
from convert.Formats.Fusion.BundleCodec.Model.BundleGraph import BundleGraph
from convert.Formats.Fusion.BundleCodec.Model.BundleLink import BundleLink
from convert.Formats.Fusion.BundleCodec.Model.BundleModel import BundleModel
from convert.Formats.Fusion.BundleCodec.Model.BundleObject import BundleObject
from convert.Formats.Fusion.BundleCodec.Model.BundleRefs import BundleRefs
from convert.Formats.Fusion.BundleCodec.Model.BundleText import BundleText
from convert.Formats.Fusion.DrawingCodec.Author.Defaults.DrawingPolicy import (
    KBundleCreator,
    KDeflateMethod,
    KDesignType,
    KDrawingType,
    KFileUrn,
    KLineageUrn,
    KServiceName,
    KStorageUrn,
)
from convert.Formats.Fusion.DrawingCodec.Author.Members.BuildManifests import (
    DesignUrl,
)
from convert.Formats.Fusion.DrawingCodec.Author.Model.DrawingSpec import DrawingSpec
from convert.Formats.Fusion.DrawingCodec.Author.Model.SaveState import SaveState
from convert.Formats.Fusion.DrawingCodec.Bundle.DrawingBundle import DrawingBundle
from convert.Formats.Fusion.DrawingCodec.Bundle.ReadDrawBundle import (
    KDescriptionName,
    KManifestName,
)
from convert.Formats.Fusion.DrawingCodec.Model.FusionDrawing import FusionDrawing
from convert.Formats.Fusion.DrawingCodec.Model.PackageSlot import PackageSlot
from convert.Formats.Fusion.DrawingCodec.Package.EntryLayout import EntryLayout
from convert.Formats.Fusion.DrawingCodec.Package.PackageLimits import (
    KDescriptorFlag,
    KUtfFlag,
)

# design object must remain consistent across callers so sheet objects retain their intended document relationships
KDesignObject = 2

# drawing object must remain consistent across callers so sheet objects retain their intended document relationships
KDrawingObject = 1


# the bundle operation needs a consistent construction rule so sheet objects retain their intended document relationships
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


# the design entry contract needs a shared interpretation so sheet objects retain their intended document relationships
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


# the drawing entry contract needs a shared interpretation so sheet objects retain their intended document relationships
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


# the stamp text contract needs a shared interpretation so sheet objects retain their intended document relationships
def StampText(StampWords: tuple[int, int]) -> str:
    TimeWord, DateWord = StampWords
    DateText = (
        f"{(DateWord >> 9) + 1980:04d}-{DateWord >> 5 & 15:02d}-{DateWord & 31:02d}"
    )
    TimeText = (
        f"{TimeWord >> 11:02d}:{TimeWord >> 5 & 63:02d}:{(TimeWord & 31) * 2:02d}"
    )
    return DateText + "T" + TimeText + "+0000"
