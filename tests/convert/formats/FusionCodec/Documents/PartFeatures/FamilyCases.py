from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.AxisSpec import AxisSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircleCurve import (
    CircleCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.CircularSpec import (
    CircularSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.HoleSpec import HoleSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MirrorSpec import (
    MirrorSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.DraftSpec import DraftSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.MoveSpec import MoveSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.OffsetSpec import (
    OffsetSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PatternSpec import (
    PatternSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PlaneSpec import (
    PlaneSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PointSpec import PointSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.RevolveSpec import (
    RevolveSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ShellSpec import ShellSpec

KBlock = ExtrudeSpec(
    (
        LineCurve((0.0, 0.0), (40.0, 0.0)),
        LineCurve((40.0, 0.0), (40.0, 30.0)),
        LineCurve((40.0, 30.0), (0.0, 30.0)),
        LineCurve((0.0, 30.0), (0.0, 0.0)),
    ),
    20.0,
    "new",
    "one",
    0.0,
    "Base sketch",
    "Base extrude",
)
KPocket = ExtrudeSpec(
    (CircleCurve((8.0, 8.0), 3.0),),
    20.0,
    "cut",
    "one",
    0.0,
    "Pocket sketch",
    "Pocket extrude",
)
KSlot = ExtrudeSpec(
    (
        LineCurve((10.0, 19.0), (14.0, 19.0)),
        ArcCurve((14.0, 22.0), 3.0, -90.0, 180.0),
        LineCurve((14.0, 25.0), (10.0, 25.0)),
        ArcCurve((10.0, 22.0), 3.0, 90.0, 180.0),
    ),
    8.0,
    "cut",
    "one",
    0.0,
    "Slot sketch",
    "Slot pocket",
)
KDisc = ExtrudeSpec(
    (CircleCurve((0.0, 0.0), 20.0),),
    12.0,
    "new",
    "one",
    0.0,
    "Disc sketch",
    "Disc extrude",
)
KRing = ExtrudeSpec(
    (CircleCurve((12.0, 0.0), 3.0),),
    6.0,
    "cut",
    "one",
    0.0,
    "Pocket sketch",
    "Pocket extrude",
)
KFamilyCases: dict[str, tuple[tuple[KPartFeature, ...], float, int, int]] = {
    "HoleFlat": ((KBlock, HoleSpec((20.0, 15.0), 8.0, 10.0)), 23.497345, 8, 14),
    "HoleCounterbore": (
        (KBlock, HoleSpec((20.0, 15.0), 6.0, 0.0, 10.0, 4.0)),
        23.233451,
        9,
        16,
    ),
    "RectPattern": (
        (KBlock, KPocket, PatternSpec(1, 3, 12.0, 2, 14.0)),
        20.60708,
        12,
        24,
    ),
    "FeatureCircPattern": (
        (KBlock, KPocket, CircularSpec(1, 2, 40.0)),
        23.03561,
        9,
        20,
    ),
    "MirrorFeature": (
        (KBlock, KPocket, PlaneSpec(20.0, "yz"), MirrorSpec(1, 2)),
        22.869027,
        8,
        16,
    ),
    "PlaneOffset": ((KBlock, PlaneSpec(15.0, "xy")), 24.0, 6, 12),
    "ConstructionSet": (
        (
            KBlock,
            PlaneSpec(15.0, "xy", "Offset plane"),
            AxisSpec((40.0, 30.0), "Edge axis"),
            PointSpec((40.0, 30.0), "Corner point"),
        ),
        24.0,
        6,
        12,
    ),
    "MultiPocketPart": (
        (
            KBlock,
            KSlot,
            HoleSpec((8.0, 8.0), 4.0),
            PatternSpec(2, 2, 12.0, 1, 10.0),
            FilletSpec((40.0, 30.0), 3.0),
            PlaneSpec(20.0, "yz"),
            MirrorSpec(1, 5),
        ),
        22.622328,
        19,
        43,
    ),
    "MultiDiscPart": (
        (
            KDisc,
            KRing,
            CircularSpec(1, 4, 360.0),
            HoleSpec((0.0, 0.0), 8.0, 0.0, 14.0, 4.0),
        ),
        13.383185,
        14,
        14,
    ),
    "ChamferTwoDistances": (
        (KBlock, ChamferSpec((40.0, 30.0), 3.0, "Corner bevel", 2.0)),
        23.94,
        7,
        15,
    ),
    "ChamferDistanceAngle": (
        (KBlock, ChamferSpec((40.0, 30.0), 3.0, "Corner bevel", 0.0, 30.0)),
        23.948038,
        7,
        15,
    ),
    "FilletTwoEdges": (
        (KBlock, FilletSpec((40.0, 30.0), 3.0, "Corner rounds", ((0.0, 0.0),))),
        23.922743,
        8,
        18,
    ),
    "ChamferTwoEdges": (
        (
            KBlock,
            ChamferSpec(
                (40.0, 30.0), 3.0, "Corner bevels", MoreCornersMm=((0.0, 0.0),)
            ),
        ),
        23.82,
        8,
        18,
    ),
    "HoleCountersink": (
        (KBlock, HoleSpec((20.0, 15.0), 6.0, SinkDiameterMm=10.0)),
        23.388437,
        8,
        15,
    ),
    "HoleCountersinkFlat": (
        (
            KBlock,
            HoleSpec(
                (20.0, 15.0), 6.0, 10.0, SinkDiameterMm=12.0, SinkAngleDegrees=82.0
            ),
        ),
        23.587153,
        9,
        15,
    ),
    "RevolveFull": ((RevolveSpec(10.0, 20.0, 0.0, 30.0),), 28.274334, 4, 4),
    "RevolveHalf": ((RevolveSpec(10.0, 20.0, 0.0, 30.0, 180.0),), 14.137167, 6, 12),
    "RevolveJoin": (
        (
            ExtrudeSpec((CircleCurve((0.0, 0.0), 25.0),), 10.0),
            RevolveSpec(10.0, 15.0, 10.0, 20.0, 360.0, "join"),
        ),
        23.561945,
        7,
        6,
    ),
    "RevolveCut": (
        (
            ExtrudeSpec((CircleCurve((0.0, 0.0), 25.0),), 10.0),
            RevolveSpec(15.0, 22.0, 6.0, 10.0, 90.0, "cut"),
        ),
        18.821282,
        8,
        14,
    ),
    "ShellOpenSide": (
        (KBlock, ShellSpec(2.0, "Open shell", SidesMm=((20.0, 0.0),))),
        5.856,
        10,
        24,
    ),
    "MoveTurn": (
        (KBlock, MoveSpec((5.0, 5.0, 2.0), "Body turn", 30.0)),
        24.0,
        6,
        12,
    ),
    "OffsetSide": (
        (KBlock, OffsetSpec(4.0, "Side offset", (40.0, 15.0))),
        26.4,
        6,
        12,
    ),
    "DraftSides": (
        (KBlock, DraftSpec(5.0, "Side draft")),
        26.531328,
        6,
        12,
    ),
}
KFamilyNames: dict[type[object], str] = {
    ExtrudeSpec: "DcExtrudeFeature",
    HoleSpec: "DcHoleFeature",
    PatternSpec: "DcRectangularPattern",
    CircularSpec: "DcCircularPattern",
    MirrorSpec: "DcMirrorPattern",
    PlaneSpec: "DcWorkPlane",
    AxisSpec: "DcWorkAxis",
    PointSpec: "DcWorkPoint",
    FilletSpec: "DcFilletEdgeFeature",
    ChamferSpec: "DcChamferFeature",
    RevolveSpec: "DcRevolveFeature",
    ShellSpec: "DcShellFeature",
    MoveSpec: "DcMoveFeature",
    OffsetSpec: "DcOffsetFacesFeature",
    DraftSpec: "DcDraftFeature",
}


def FamilySpec(Features: tuple[KPartFeature, ...]) -> DocumentSpec:
    return DocumentSpec(
        Title="Kit family",
        ParamName="height",
        LengthMm=20.0,
        ProfileKind="part",
        BodyName="Body1",
        Features=Features,
    )
