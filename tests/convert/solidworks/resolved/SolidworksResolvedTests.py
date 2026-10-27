# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import math as MathInfo
from pathlib import Path as FilePath
import xml.etree.ElementTree as ElementTree
import pytest as PytestLib
from convert.adapters.solidworks.container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.container.Format import (
    KEYWORDS_STREAM as Stream,
    RESOLVED_FEATURES_STREAM as StreamA,
)
from convert.adapters.solidworks.resolved.Core import (
    BLIND_END_CONDITION as Condition,
    BOSS_FLAGS as Flags,
    BOSS_KIND as KindInfo,
    CIRCLE_POINT_ANGLE_DEGREES as Degrees,
    CUT_FLAGS as FlagsA,
    CUT_KIND as KindInfoA,
    FEATURE_FLAGS_MASK as MaskInfo,
    FIRST_FEATURE_REVERSE_DISTANCE as DistanceA,
    FULL_CIRCLE_DEGREES as DegreesA,
    LATER_FEATURE_REVERSE_DISTANCE as DistanceC,
    LOFT_FLAGS as FlagsC,
    LOFT_KIND as KindInfoB,
    MID_PLANE_END_CONDITION as ConditionA,
    ROUND_KIND as KindInfoC,
    SKETCH_FLAGS as FlagsF,
    SKETCH_ON_CURVE_ROLE as RoleInfo,
    SKETCH_POINT_CLASS as Class,
    SWEEP_FLAGS as FlagsG,
    SWEEP_KIND as KindInfoD,
    SWEEP_SINGLE_PROFILE_FLAGS as FlagsH,
    FeatureEdit,
    circle_circumference_point_mm as CircleCPM,
    circle_radius_mm as CircleRadiusMm,
    class_records as ClassRecords,
    dimension_scalars as DimensionScalars,
    locate_features as LocateFeatures,
    locate_rectangle_pad as LocateRectanglePad,
    name_records as NameRecords,
    patch_features as PatchFeatures,
    patch_sketch_arcs as PatchSketchArcs,
    rectangle_corners_mm as RectangleCornersMm,
    sketch_arcs as SketchArcs,
    sketch_coordinates as SketchCoordinates,
    sketch_points as SketchPoints,
    tree_nodes as TreeNodes,
)

# centralizes shared evidence so every related assertion uses one value
KCorpusA = FilePath(__file__).resolve().parents[4] / ".rescratch" / "corpus2"

# centralizes shared evidence so every related assertion uses one value
KParts = KCorpusA / "parts"

# centralizes shared evidence so every related assertion uses one value
KPatched = KCorpusA / "patched"

# centralizes shared evidence so every related assertion uses one value
KCorpus = (
    FilePath(__file__).resolve().parents[4]
    / "examples"
    / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
)

# centralizes shared evidence so every related assertion uses one value
KPrefix = "<MOD-DIAM>"

# centralizes shared evidence so every related assertion uses one value
KPrefixA = "R"

# centralizes shared evidence so every related assertion uses one value
KPartInfo = "CUTBASE_cd5"

# centralizes shared evidence so every related assertion uses one value
KExtrusions = (
    (35, KindInfo, 38.0),
    (188, KindInfo, 18.0),
    (204, KindInfo, 30.7),
    (214, KindInfoA, 46.7),
    (228, KindInfoA, 5.0),
    (250, KindInfoA, 9.0),
)

# centralizes shared evidence so every related assertion uses one value
KChamfers = ((231, 2.0), (236, 1.0), (253, 1.0), (256, 2.0))

# centralizes shared evidence so every related assertion uses one value
KFeaturesA = {
    45: KindInfoB,
    48: KindInfoB,
    64: KindInfoD,
    189: KindInfoD,
    210: KindInfoD,
    234: KindInfoD,
    240: KindInfoD,
}

# centralizes shared evidence so every related assertion uses one value
KTypeInfo = {
    "Sweep": KindInfoD,
    "Cut-Sweep": KindInfoD,
    "Loft": KindInfoB,
    "Cut-Loft": KindInfoB,
    "Chamfer": KindInfoC,
    "Fillet": KindInfoC,
}

# centralizes shared evidence so every related assertion uses one value
KCorpusParts = PytestLib.mark.skipif(
    not KParts.is_dir(),
    reason="the SOLIDWORKS multi-feature corpus is not present in this checkout",
)

# centralizes shared evidence so every related assertion uses one value
KCorpusPatched = PytestLib.mark.skipif(
    not KPatched.is_dir(),
    reason="the proven round-trip artefacts are not present in this checkout",
)

# centralizes shared evidence so every related assertion uses one value
KFeatures = {
    "CUTBASE_cd3": ((KindInfo, 10.0, 4), (KindInfoA, 3.0, 4)),
    "CUTBASE_cd5": ((KindInfo, 10.0, 4), (KindInfoA, 5.0, 4)),
    "CUTBASE_cd7": ((KindInfo, 10.0, 4), (KindInfoA, 7.0, 4)),
    "CUTBASE_s8": ((KindInfo, 10.0, 4), (KindInfoA, 5.0, 4)),
    "CUTBASE_s10": ((KindInfo, 10.0, 4), (KindInfoA, 5.0, 4)),
    "CUTBASE_s14": ((KindInfo, 10.0, 4), (KindInfoA, 5.0, 4)),
    "CUTTHROUGH_s10": ((KindInfo, 10.0, 4), (KindInfoA, None, 4)),
    "CUTFACE_d5": ((KindInfo, 10.0, 4), (KindInfoA, 5.0, 4)),
    "CUTMID_d5": ((KindInfo, 10.0, 4), (KindInfoA, 5.0, 4)),
    "PADPLANE_rev_d5": ((KindInfo, 10.0, 4), (KindInfo, 5.0, 4)),
    "TWOPAD_d3": ((KindInfo, 10.0, 4), (KindInfo, 3.0, 4)),
    "TWOPAD_d5": ((KindInfo, 10.0, 4), (KindInfo, 5.0, 4)),
    "TWOPAD_d8": ((KindInfo, 10.0, 4), (KindInfo, 8.0, 4)),
    "THREEFEATURE_pad_cut_pad": (
        (KindInfo, 10.0, 4),
        (KindInfoA, 5.0, 4),
        (KindInfo, 4.0, 4),
    ),
    "CIRCLECUT_r4": ((KindInfo, 10.0, 4), (KindInfoA, 5.0, 0)),
    "CIRCLECUT_r6": ((KindInfo, 10.0, 4), (KindInfoA, 5.0, 0)),
    "CONTROL2_A": ((KindInfo, 10.0, 4), (KindInfoA, 5.0, 4)),
    "CONTROL2_B": ((KindInfo, 10.0, 4), (KindInfoA, 5.0, 4)),
    "CONTROL2PAD_A": ((KindInfo, 10.0, 4), (KindInfo, 5.0, 4)),
    "CONTROL2PAD_B": ((KindInfo, 10.0, 4), (KindInfo, 5.0, 4)),
}

# centralizes shared evidence so every related assertion uses one value
KConditions = {
    "CUTBASE_cd5": ((False, Condition), (True, Condition)),
    "CUTMID_d5": ((False, Condition), (True, ConditionA)),
    "CUTFACE_d5": ((False, Condition), (False, Condition)),
    "PADPLANE_rev_d5": ((False, Condition), (True, Condition)),
    "TWOPAD_d5": ((False, Condition), (False, Condition)),
    "CIRCLECUT_r4": ((False, Condition), (True, Condition)),
    "THREEFEATURE_pad_cut_pad": (
        (False, Condition),
        (True, Condition),
        (False, Condition),
    ),
}

# centralizes shared evidence so every related assertion uses one value
KTrips = (
    (
        "A_cutbase_both_features",
        "CUTBASE_cd5",
        {0: (50.0, 30.0, 12.0), 1: (14.0, 14.0, 7.0)},
    ),
    ("B_cutbase_second_feature_only", "CUTBASE_cd5", {1: (8.0, 8.0, 3.0)}),
    (
        "C_twopad_both_features",
        "TWOPAD_d5",
        {0: (45.0, 25.0, 11.0), 1: (12.0, 12.0, 6.0)},
    ),
    (
        "D_threefeature_all_three",
        "THREEFEATURE_pad_cut_pad",
        {0: (60.0, 25.0, 14.0), 1: (12.0, 12.0, 6.0), 2: (6.0, 6.0, 3.0)},
    ),
)


# keeps this focused behavior isolated so regressions remain immediately visible
def CorpusStream(NameText: str) -> bytes:
    Archive = SldprtArchive.from_bytes((KParts / f"{NameText}.SLDPRT").read_bytes())
    return Archive.require(StreamA)


# keeps this focused behavior isolated so regressions remain immediately visible
def AuthoredParts() -> tuple[FilePath, ...]:
    return tuple(
        sorted(
            (
                TargetPath
                for TargetPath in KCorpus.glob("*.SLDPRT")
                if not TargetPath.name.startswith("~$")
            )
        )
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def AuthoredRS(NameText: str) -> bytes:
    Archive = SldprtArchive.from_bytes((KCorpus / f"{NameText}.SLDPRT").read_bytes())
    return Archive.require(StreamA)


# keeps this focused behavior isolated so regressions remain immediately visible
def Keywords(BlobInfo: bytes) -> ElementTree.Element:
    TextInfo = BlobInfo.decode("utf-8", errors="replace")
    return ElementTree.fromstring(TextInfo[TextInfo.index("<?xml") :])


# keeps this focused behavior isolated so regressions remain immediately visible
def AuthoredK(NameText: str) -> ElementTree.Element:
    Archive = SldprtArchive.from_bytes((KCorpus / f"{NameText}.SLDPRT").read_bytes())
    return Keywords(Archive.require(Stream))


# keeps this focused behavior isolated so regressions remain immediately visible
def AuthoredNodes(KeywordsA: ElementTree.Element) -> dict[int, ElementTree.Element]:
    return {
        int(Element.get("id", "-1")): Element
        for Element in KeywordsA
        if Element.get("id", "").isdigit()
    }


# keeps this focused behavior isolated so regressions remain immediately visible
def AuthoredD(Element: ElementTree.Element, NameText: str) -> str | None:
    for Dimension in Element:
        if Dimension.tag == "Dimension" and Dimension.get("Name") == NameText:
            return Dimension.text
    return None


# keeps this focused behavior isolated so regressions remain immediately visible
def AuthoredRadiiMm(Element: ElementTree.Element) -> tuple[float, ...]:
    Radii: list[float] = []
    for Dimension in Element:
        TextInfo = (Dimension.text or "").strip()
        if Dimension.tag != "Dimension" or not TextInfo:
            continue
        if TextInfo.startswith(KPrefix):
            Radii.append(float(TextInfo[len(KPrefix) :]) / 2.0)
        elif (
            TextInfo.startswith(KPrefixA)
            and TextInfo[len(KPrefixA) :].replace(".", "", 1).isdigit()
        ):
            Radii.append(float(TextInfo[len(KPrefixA) :]))
    return tuple(Radii)


# keeps this focused behavior isolated so regressions remain immediately visible
def AuthoredRBF(KeywordsA: ElementTree.Element) -> tuple[float, ...]:
    return tuple(
        (Radius for Element in KeywordsA for Radius in AuthoredRadiiMm(Element))
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def PatchedStream(NameText: str) -> bytes:
    Archive = SldprtArchive.from_bytes((KPatched / f"{NameText}.SLDPRT").read_bytes())
    return Archive.require(StreamA)


# keeps this focused behavior isolated so regressions remain immediately visible
def RectanglePS() -> bytes:
    return CorpusStream(KPartInfo)


# keeps this focused behavior isolated so regressions remain immediately visible
def CentredCorners(WidthMm: float, HeightMm: float) -> tuple[tuple[float, float], ...]:
    return RectangleCornersMm(
        -WidthMm / 2.0, -HeightMm / 2.0, WidthMm / 2.0, HeightMm / 2.0
    )


# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
def TestWRPIRTTGL() -> None:
    Resolved = RectanglePS()
    Features = LocateFeatures(Resolved)
    Layout = LocateRectanglePad(Resolved)
    assert Layout is not None
    assert len(Features) == 2
    Feature = Features[0]
    assert Feature.kind == KindInfo
    assert Feature.flags == Flags
    assert Feature.feature_id == 32
    assert Feature.sketch_name == "Sketch1"
    assert Feature.sketch_id == 26
    assert Feature.depth_offset == Layout.depth_offset
    assert Feature.reverse_offset == Layout.reverse_offset
    assert Feature.end_condition_offset == Layout.end_condition_offset
    assert tuple((Point.offset for Point in Feature.points)) == tuple(
        (XOffset for XOffset, _ in Layout.point_offsets)
    )
    assert Feature.corners_mm == Layout.corners_mm
    assert Feature.bounds_mm == (-20.0, -10.0, 20.0, 10.0)
    assert Feature.depth_mm == PytestLib.approx(10.0)
    assert Feature.reversed is False
    assert Feature.end_condition_code == Condition
    assert Features[1].kind == KindInfoA
    assert Features[1].depth_offset != Layout.depth_offset
    assert Features[1].corners_mm != Layout.corners_mm


# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
def TestNRETTNADS() -> None:
    Resolved = RectanglePS()
    RecordList = NameRecords(Resolved)
    Nodes = TreeNodes(Resolved)
    assert {NodeInfo.name for NodeInfo in Nodes} >= {
        "Sketch1",
        "Boss-Extrude1",
        "Sketch2",
        "Cut-Extrude1",
    }
    assert {NodeInfo.offset for NodeInfo in Nodes} <= {
        RecordInfo.offset for RecordInfo in RecordList
    }
    assert [
        NodeInfo.flags for NodeInfo in Nodes if NodeInfo.name == "Boss-Extrude1"
    ] == [Flags]
    assert [
        NodeInfo.flags for NodeInfo in Nodes if NodeInfo.name == "Cut-Extrude1"
    ] == [FlagsA]
    assert [NodeInfo.flags for NodeInfo in Nodes if NodeInfo.name == "Sketch1"] == [
        FlagsF
    ]
    assert [NodeInfo.flags for NodeInfo in Nodes if NodeInfo.name == "Sketch2"] == [
        FlagsF
    ]
    Scalars = DimensionScalars(Resolved)
    Depths = [Scalar for Scalar in Scalars if Scalar.name.startswith("D")]
    assert [Scalar.value_mm for Scalar in Depths] == [
        PytestLib.approx(10.0),
        PytestLib.approx(5.0),
    ]
    assert len(SketchPoints(Resolved)) == 8


# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
def TestPFRAWRP() -> None:
    Resolved = RectanglePS()
    Corners = RectangleCornersMm(-11.0, -6.0, 19.0, 8.0)
    Patched = PatchFeatures(
        Resolved,
        {
            0: FeatureEdit(
                corners_mm=Corners,
                depth_mm=7.5,
                reversed=True,
                end_condition_code=ConditionA,
                update_depth_copies=True,
            )
        },
    )
    assert len(Patched) == len(Resolved)
    Feature = LocateFeatures(Patched)[0]
    assert Feature.corners_mm == Corners
    assert Feature.depth_mm == PytestLib.approx(7.5)
    assert Feature.reversed is True
    assert Feature.end_condition_code == ConditionA
    Layout = LocateRectanglePad(Patched)
    assert Layout is not None
    assert Layout.corners_mm == Corners
    assert Layout.depth_mm == PytestLib.approx(7.5)
    assert Layout.reversed is True
    assert Layout.end_condition_code == ConditionA
    assert PatchFeatures(Resolved, {}) == Resolved


# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
def TestPFRETSCH() -> None:
    Resolved = RectanglePS()
    Rejected = (
        {9: FeatureEdit(depth_mm=5.0)},
        {0: FeatureEdit(corners_mm=((0.0, 0.0),))},
        {0: FeatureEdit(corners_mm=CentredCorners(MathInfo.inf, 4.0))},
        {0: FeatureEdit(depth_mm=0.0)},
        {0: FeatureEdit(depth_mm=MathInfo.nan)},
        {0: FeatureEdit(end_condition_code=1)},
        {0: FeatureEdit(update_depth_copies=True)},
    )
    for Edits in Rejected:
        with PytestLib.raises(SldprtFormatError):
            _ = PatchFeatures(Resolved, Edits)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBFPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/resolved/boss/fillet/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBCPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/resolved/boss/chamfer/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBSPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/resolved/boss/shell/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBLPPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/resolved/boss/pattern/linear/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBCPPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/resolved/boss/pattern/circular/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
@PytestLib.mark.parametrize("NameText", sorted(KFeatures))
def TestCPLEFWIMP(NameText: str) -> None:
    Features = LocateFeatures(CorpusStream(NameText))
    Expected = KFeatures[NameText]
    assert len(Features) == len(Expected)
    for Feature, (KindInfoE, DepthMm, PointCount) in zip(
        Features, Expected, strict=True
    ):
        assert Feature.kind == KindInfoE
        assert len(Feature.points) == PointCount
        if DepthMm is None:
            assert Feature.depth_mm is None
            assert Feature.depth_offset is None
        else:
            assert Feature.depth_mm == PytestLib.approx(DepthMm)


# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
def TestCSOFLBRABD() -> None:
    Features = LocateFeatures(CorpusStream("CUTBASE_s14"))
    assert [Feature.kind for Feature in Features] == [KindInfo, KindInfoA]
    assert [Feature.feature_id for Feature in Features] == [32, 40]
    assert [Feature.sketch_name for Feature in Features] == ["Sketch1", "Sketch2"]
    assert [Feature.sketch_id for Feature in Features] == [26, 33]
    assert Features[0].corners_mm == RectangleCornersMm(-20.0, -10.0, 20.0, 10.0)
    assert Features[0].depth_mm == PytestLib.approx(10.0)
    assert Features[1].corners_mm == RectangleCornersMm(-7.0, -7.0, 7.0, 7.0)
    assert Features[1].depth_mm == PytestLib.approx(5.0)
    assert Features[0].depth_offset is not None
    assert Features[1].depth_offset is not None
    assert Features[0].depth_offset < Features[1].depth_offset


# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
def TestTFIRWACM() -> None:
    Resolved = CorpusStream("THREEFEATURE_pad_cut_pad")
    Features = LocateFeatures(Resolved)
    assert len(Features) == 3
    assert [Feature.kind for Feature in Features] == [KindInfo, KindInfoA, KindInfo]
    assert [Feature.feature_id for Feature in Features] == [32, 40, 47]
    assert [Feature.sketch_id for Feature in Features] == [26, 33, 41]
    assert [Feature.depth_mm for Feature in Features] == [
        PytestLib.approx(10.0),
        PytestLib.approx(5.0),
        PytestLib.approx(4.0),
    ]
    assert Features[2].corners_mm == RectangleCornersMm(-4.0, -4.0, 4.0, 4.0)
    NameList = [RecordInfo.name for RecordInfo in ClassRecords(Resolved)]
    assert NameList.count("moICE_c") == 1
    assert NameList.count("moExtrusion_c") == 1
    assert "moCut_c" not in NameList


# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
def TestTAFHNDSBKIS() -> None:
    Resolved = CorpusStream("CUTTHROUGH_s10")
    Features = LocateFeatures(Resolved)
    assert len(Features) == 2
    assert Features[1].depth_offset is None
    assert Features[1].depth_mm is None
    assert Features[1].depth_copy_offsets == ()
    assert Features[1].reverse_offset is None
    assert Features[1].end_condition_offset is None
    assert Features[1].corners_mm == RectangleCornersMm(-5.0, -5.0, 5.0, 5.0)
    Corners = RectangleCornersMm(-6.0, -6.0, 6.0, 6.0)
    Patched = PatchFeatures(Resolved, {1: FeatureEdit(corners_mm=Corners)})
    assert LocateFeatures(Patched)[1].corners_mm == Corners
    with PytestLib.raises(SldprtFormatError):
        _ = PatchFeatures(Resolved, {1: FeatureEdit(depth_mm=4.0)})


# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
@PytestLib.mark.parametrize("NameText", sorted(KConditions))
def TestDAECFRBFTC(NameText: str) -> None:
    Features = LocateFeatures(CorpusStream(NameText))
    Expected = KConditions[NameText]
    assert len(Features) == len(Expected)
    for Feature, (Reverse, CodeInfo) in zip(Features, Expected, strict=True):
        assert Feature.reversed is Reverse
        assert Feature.end_condition_code == CodeInfo
        assert Feature.depth_offset is not None
        assert Feature.reverse_offset is not None
        DistanceD = Feature.depth_offset - Feature.reverse_offset
        assert DistanceD == (DistanceA if Feature.ordinal == 0 else DistanceC)


# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
def TestPFBVATC() -> None:
    Resolved = CorpusStream("CUTMID_d5")
    Patched = PatchFeatures(
        Resolved,
        {
            1: FeatureEdit(
                depth_mm=9.0,
                reversed=False,
                end_condition_code=Condition,
                update_depth_copies=True,
            )
        },
    )
    assert len(Patched) == len(Resolved)
    Features = LocateFeatures(Patched)
    assert Features[1].depth_mm == PytestLib.approx(9.0)
    assert Features[1].reversed is False
    assert Features[1].end_condition_code == Condition
    assert Features[0].depth_mm == PytestLib.approx(10.0)
    assert Features[0].end_condition_code == Condition


# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
@KCorpusPatched
@PytestLib.mark.parametrize(("NameText", "Donor", "SpecInfo"), KTrips)
def TestPFRTPRTS(
    NameText: str, Donor: str, SpecInfo: dict[int, tuple[float, float, float]]
) -> None:
    Resolved = CorpusStream(Donor)
    Edits = {
        Ordinal: FeatureEdit(
            corners_mm=CentredCorners(WidthMm, HeightMm), depth_mm=DepthMm
        )
        for Ordinal, (WidthMm, HeightMm, DepthMm) in SpecInfo.items()
    }
    assert PatchFeatures(Resolved, Edits) == PatchedStream(NameText)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTACIPITC() -> None:
    assert KCorpus.is_dir()
    assert len(AuthoredParts()) >= 57


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBBACFMTKD() -> None:
    Features = LocateFeatures(AuthoredRS("BIELA"))
    Authored = AuthoredNodes(AuthoredK("BIELA"))
    Extrusions = tuple(
        (Feature for Feature in Features if Feature.kind in {KindInfo, KindInfoA})
    )
    assert tuple(
        ((Feature.feature_id, Feature.kind) for Feature in Extrusions)
    ) == tuple(((Identifier, KindInfoE) for Identifier, KindInfoE, _ in KExtrusions))
    for Feature, (Identifier, _, DepthMm) in zip(Extrusions, KExtrusions, strict=True):
        Element = Authored[Identifier]
        assert Element.tag == "Extrusion"
        assert float(AuthoredD(Element, "D1") or "nan") == PytestLib.approx(DepthMm)
        assert Feature.depth_mm == PytestLib.approx(DepthMm)
        assert Feature.flags & MaskInfo == (
            Flags if Feature.kind == KindInfo else FlagsA
        )
        assert Feature.flags & 2147483648
        assert Feature.sketch_id is not None
        assert Authored[Feature.sketch_id].tag == "Sketch"


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBCACARF() -> None:
    Features = LocateFeatures(AuthoredRS("BIELA"))
    Authored = AuthoredNodes(AuthoredK("BIELA"))
    Rounds = tuple((Feature for Feature in Features if Feature.kind == KindInfoC))
    assert tuple((Feature.feature_id for Feature in Rounds)) == tuple(
        (Identifier for Identifier, _ in KChamfers)
    )
    for Feature, (Identifier, DistanceMm) in zip(Rounds, KChamfers, strict=True):
        Element = Authored[Identifier]
        assert KTypeInfo[Element.get("Type", "")] == KindInfoC
        assert float(AuthoredD(Element, "D1") or "nan") == PytestLib.approx(DistanceMm)
        assert Feature.depth_mm == PytestLib.approx(DistanceMm)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTTSALMTKT() -> None:
    Features = LocateFeatures(AuthoredRS("Turbo Tube"))
    Authored = AuthoredNodes(AuthoredK("Turbo Tube"))
    Swept = {
        Feature.feature_id: Feature
        for Feature in Features
        if Feature.kind in {KindInfoD, KindInfoB}
    }
    assert {
        Identifier: Feature.kind for Identifier, Feature in Swept.items()
    } == KFeaturesA
    for Identifier, Feature in Swept.items():
        Element = Authored[Identifier]
        assert KTypeInfo[Element.get("Type", "")] == Feature.kind
        assert Feature.flags & MaskInfo in {FlagsG, FlagsH, FlagsC}


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBCPDTAD() -> None:
    Resolved = AuthoredRS("BIELA")
    Authored = AuthoredNodes(AuthoredK("BIELA"))
    Features = LocateFeatures(Resolved)
    Circular = {
        Feature.feature_id: Feature.radii_mm for Feature in Features if Feature.arcs
    }
    assert Circular == {
        35: (PytestLib.approx(22.2), PytestLib.approx(17.8)),
        214: (PytestLib.approx(4.5), PytestLib.approx(4.5)),
        250: (PytestLib.approx(1.25),),
    }
    for Feature in Features:
        if not Feature.arcs:
            continue
        assert Feature.sketch_id is not None
        Expected = AuthoredRadiiMm(Authored[Feature.sketch_id])
        assert Expected
        for ArcInfo in Feature.arcs:
            assert any(
                (
                    MathInfo.isclose(
                        ArcInfo.radius_mm, Radius, rel_tol=1e-09, abs_tol=1e-09
                    )
                    for Radius in Expected
                )
            )
            assert ArcInfo.start_angle_degrees == PytestLib.approx(Degrees)
            assert ArcInfo.sweep_angle_degrees == DegreesA
            assert ArcInfo.full_circle
    assert len(SketchArcs(Resolved)) == 5


# keeps this focused behavior isolated so regressions remain immediately visible
def NamedTARAACFBAS() -> None:
    Resolved = AuthoredRS("BIELA")
    Coordinates = {
        Coordinate.offset: Coordinate for Coordinate in SketchCoordinates(Resolved)
    }
    for ArcInfo in SketchArcs(Resolved):
        Centre = Coordinates[ArcInfo.centre_offset]
        RimInfo = Coordinates[ArcInfo.point_offset]
        assert ArcInfo.point_offset > ArcInfo.centre_offset
        assert RimInfo.role == RoleInfo
        assert RimInfo.geometry_class == Class
        assert (Centre.x_mm, Centre.y_mm) == ArcInfo.centre_mm
        assert CircleRadiusMm(
            RimInfo.x_mm - Centre.x_mm, RimInfo.y_mm - Centre.y_mm
        ) == PytestLib.approx(ArcInfo.radius_mm)
        OffsetX, OffsetY = CircleCPM(ArcInfo.radius_mm)
        assert RimInfo.x_mm == PytestLib.approx(Centre.x_mm + OffsetX)
        assert RimInfo.y_mm == PytestLib.approx(Centre.y_mm + OffsetY)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestACCRAWTAD() -> None:
    Decoded = 0
    Matched = 0
    FilesWithArcs = 0
    for TargetPath in AuthoredParts():
        Archive = SldprtArchive.from_bytes(TargetPath.read_bytes())
        Streams = Archive.streams
        Resolved = Streams.get(StreamA)
        KeywordsA = Streams.get(Stream)
        if Resolved is None or KeywordsA is None:
            continue
        Expected = AuthoredRBF(Keywords(KeywordsA))
        ArcsInfo = SketchArcs(Resolved)
        FilesWithArcs += 1 if ArcsInfo else 0
        for ArcInfo in ArcsInfo:
            Decoded += 1
            assert ArcInfo.radius_mm > 0.0
            assert MathInfo.isfinite(ArcInfo.radius_mm)
            Matched += any(
                (
                    MathInfo.isclose(
                        ArcInfo.radius_mm, Radius, rel_tol=1e-09, abs_tol=1e-09
                    )
                    for Radius in Expected
                )
            )
    assert Decoded >= 480
    assert FilesWithArcs >= 49
    assert Matched / Decoded >= 0.85


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPSARAACR() -> None:
    Resolved = AuthoredRS("BIELA")
    ArcsInfo = SketchArcs(Resolved)
    Patched = PatchSketchArcs(Resolved, {0: 25.0, 4: 3.5})
    assert len(Patched) == len(Resolved)
    Relocated = SketchArcs(Patched)
    assert len(Relocated) == len(ArcsInfo)
    assert Relocated[0].radius_mm == PytestLib.approx(25.0)
    assert Relocated[4].radius_mm == PytestLib.approx(3.5)
    assert Relocated[1].radius_mm == PytestLib.approx(ArcsInfo[1].radius_mm)
    assert Relocated[0].centre_mm == ArcsInfo[0].centre_mm
    assert PatchSketchArcs(Resolved, {}) == Resolved
    for Radii in ({len(ArcsInfo): 5.0}, {0: 0.0}, {0: MathInfo.inf}, {0: MathInfo.nan}):
        with PytestLib.raises(SldprtFormatError):
            _ = PatchSketchArcs(Resolved, Radii)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPFRTROACP() -> None:
    Resolved = AuthoredRS("BIELA")
    Features = LocateFeatures(Resolved)
    Circular = next((Feature for Feature in Features if Feature.feature_id == 214))
    ExpectedCentres = ((3.0, -2.0), (7.5, 4.0))
    Patched = PatchFeatures(
        Resolved,
        {
            Circular.ordinal: FeatureEdit(
                radii_mm=(6.0, 6.5), arc_centres_mm=ExpectedCentres, depth_mm=44.0
            )
        },
    )
    assert len(Patched) == len(Resolved)
    Relocated = LocateFeatures(Patched)[Circular.ordinal]
    assert Relocated.feature_id == 214
    assert Relocated.radii_mm == PytestLib.approx((6.0, 6.5))
    for ArcData, ExpectedCentre in zip(Relocated.arcs, ExpectedCentres, strict=True):
        assert ArcData.centre_mm == PytestLib.approx(ExpectedCentre)
    assert Relocated.depth_mm == PytestLib.approx(44.0)
    assert Relocated.bounds_mm is not None
    Rejected = (
        {Circular.ordinal: FeatureEdit(radii_mm=(6.0,))},
        {Circular.ordinal: FeatureEdit(radii_mm=(6.0, -1.0))},
        {Circular.ordinal: FeatureEdit(radii_mm=(6.0, MathInfo.nan))},
        {Features[5].ordinal: FeatureEdit(radii_mm=(6.0,))},
    )
    for Edits in Rejected:
        with PytestLib.raises(SldprtFormatError):
            _ = PatchFeatures(Resolved, Edits)


# keeps this focused behavior isolated so regressions remain immediately visible
@KCorpusParts
@PytestLib.mark.parametrize(
    ("NameText", "RadiusMm"), (("CIRCLECUT_r4", 4.0), ("CIRCLECUT_r6", 6.0))
)
def TestCCRIRTLF(NameText: str, RadiusMm: float) -> None:
    Resolved = CorpusStream(NameText)
    Features = LocateFeatures(Resolved)
    assert [Feature.kind for Feature in Features] == [KindInfo, KindInfoA]
    Circular = Features[1]
    assert Circular.points == ()
    assert len(Circular.arcs) == 1
    ArcInfo = Circular.arcs[0]
    assert ArcInfo.radius_mm == PytestLib.approx(RadiusMm)
    assert ArcInfo.centre_mm == PytestLib.approx((0.0, 0.0))
    assert Circular.bounds_mm == PytestLib.approx(
        (
            -RadiusMm,
            -RadiusMm,
            RadiusMm,
            RadiusMm,
        )
    )
    Patched = PatchFeatures(Resolved, {1: FeatureEdit(radii_mm=(RadiusMm + 1.5,))})
    assert LocateFeatures(Patched)[1].arcs[0].radius_mm == PytestLib.approx(
        RadiusMm + 1.5
    )
