# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from pathlib import Path as FilePath
import pytest as PytestLib
from convert.adapters.solidworks import (
    SldprtArchive,
    build_sldprt as BuildSldprt,
    read_sldprt as ReadSldprt,
)
from convert.adapters.solidworks.core.Adapter import (
    SldprtAdapter,
)
from convert.adapters.solidworks.container.Container import (
    container_signatures as ContainerSignatures,
)
from convert.adapters.solidworks.core.Native import (
    decode_native_model as DecodeNativeModel,
)
from interchange import (
    BooleanOperation,
    CadDocument,
    Capability,
    NativeFeatureDefinition,
    NativeGeometry,
    PayloadRole,
)
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureExtrude import ExtrudeFeature as ExtrusionFeature
from interchange.features.FeatureKinds import FilletFeature
from interchange.geometry.models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.models.Sketch import SketchEntity

# centralizes shared evidence so every related assertion uses one value
KSample = (
    FilePath(__file__).resolve().parents[4] / "examples" / ".SLDPRT" / "example.SLDPRT"
)

# centralizes shared evidence so every related assertion uses one value
KCorpus = FilePath(__file__).resolve().parents[4] / "examples" / "Random"

# centralizes shared evidence so every related assertion uses one value
KTwoZeroTwoSix = frozenset(
    (
        ItemValueA.casefold()
        for ItemValueA in "\nAsmExploder\nCompExplodeStep\nExplodeLineProfileFeature\nInContextFeatHolder\nMagneticGroundPlane\nMateCamTangent\nMateCoincident\nMateConcentric\nMateDistanceDim\nMateGearDim\nMateHinge\nMateInPlace\nMateLimitDistanceDim\nMateLinearCoupler\nMateLock\nMateParallel\nMatePerpendicular\nMatePlanarAngleDim\nMateProfileCenter\nMateRackPinionDim\nMateScrew\nMateSlot\nMateSymmetric\nMateTangent\nMateUniversalJoint\nMateWidth\nPosGroupFolder\nReference\nReferencePattern\nSmartComponentFeature\nAdvHoleWzd\nAPattern\nBaseBody\nBending\nBlend\nBlendCut\nBodyExplodeStep\nBoss\nBossThin\nChamfer\nCirPattern\nCombineBodies\nCosmeticThread\nCosmeticWeldBead\nCreateAssemFeat\nCurvePattern\nCut\nCutThin\nDeform\nDeleteBody\nDelFace\nDerivedCirPattern\nDerivedHolePattern\nDerivedLPattern\nDimPattern\nDome\nDraft\nEdgeMerge\nEmboss\nExtrusion\nFillet\nHelix\nHoleSeries\nHoleWzd\nImported\nLocalChainPattern\nLocalCirPattern\nLocalCurvePattern\nLocalLPattern\nLocalSketchPattern\nLPattern\nMacroFeature\nMirrorCompFeat\nMirrorPattern\nMirrorSolid\nMirrorStock\nMoveCopyBody\nNetBlend\nPrtExploder\nPunch\nReplaceFace\nRevCut\nRevolution\nRevolutionThin\nRib\nRip\nSculpt\nShape\nShell\nSketchHole\nSketchPattern\nSplit\nSplitBody\nStock\nSweep\nSweepCut\nSweepThread\nTablePattern\nThicken\nThickenCut\nVarFillet\nBendTableAchor\nBomFeat\nBomTemplate\nDetailCircle\nDrBreakoutSectionLine\nDrSectionLine\nGeneralTableAnchor\nHoleTableAnchor\nLiveSection\nPunchTableAnchor\nRevisionTableAnchor\nWeldmentTableAnchor\nFamilyTableFeat\nWeldTableAnchor\nBlockFolder\nCommentsFolder\nCosmeticWeldSubFolder\nCutListFolder\nFeatSolidBodyFolder\nFeatSurfaceBodyFolder\nFtrFolder\nInsertedFeatureFolder\nMateReferenceGroupFolder\nProfileFtrFolder\nRefAxisFtrFolder\nRefPlaneFtrFolder\nSketchSliceFolder\nSolidBodyFolder\nSubAtomFolder\nSubWeldFolder\nSurfaceBodyFolder\nTemplateFlatPattern\nMBimport\nAttribute\nBlockDef\nCurveInFile\nGridFeature\nLibraryFeature\nScale\nSensor\nViewBodyFeature\nCavity\nMoldCoreCavitySolids\nMoldPartingGeom\nMoldPartLine\nMoldShutOffSrf\nSideCore\nXformStock\nAEM3DContact\nAEMGravity\nAEMLinearDamper\nAEMLinearMotor\nAEMLinearSpring\nAEMRotationalMotor\nAEMTorque\nAEMTorsionalDamper\nAEMTorsionalSpring\nSimPlotFeature\nSimPlotXAxisFeature\nSimPlotYAxisFeature\nSimResultFolder\nBoundingBox\nCenterOfMass\nCoordSys\nGroundPlane\nRefAxis\nRefPlane\nAmbientLight\nCameraFeature\nDirectionLight\nPointLight\nSpotLight\nSMBaseFlange\nBreakCorner\nCornerTrim\nCrossBreak\nEdgeFlange\nFlatPattern\nFlattenBends\nFold\nFormToolInstance\nHem\nJog\nLoftedBend\nNormalCut\nOneBend\nProcessBends\nSheetMetal\nSketchBend\nSM3dBend\nSMGusset\nSMMiteredFlange\nSolidToSheetMetal\nTemplateSheetMetal\nToroidalBend\nUnFold\n3DProfileFeature\n3DSplineCurve\nCompositeCurve\nImportedCurve\nPLine\nProfileFeature\nRefCurve\nRefPoint\nSketchBlockDef\nSketchBlockInst\nSketchBitmap\nBlendRefSurface\nExtendRefSurface\nExtruRefSurface\nFillRefSurface\nFlattenSurface\nMidRefSurface\nOffsetRefSuface\nPlanarSurface\nRadiateRefSurface\nRefSurface\nRevolvRefSurf\nRuledSrfFromEdge\nSewRefSurface\nSurfCut\nSweepRefSurface\nTrimRefSurface\nUnTrimRefSurf\nEndCap\nStrctSysBtwPtsMbrFeat\nStrctSysCnrFeat\nStrctSysCnrGrpFeat\nStrctSysCnrMgmtFeat\nStrctSysFeat\nStrctSysGrpFeat\nStrctSysPathSegMbrFeat\nStrctSysPtToMem\nStrctSysRefPlnMbrFeat\nStrctSysSkPtLenMbrFeat\nStrctSysSupPlnMbrFeat\nStrctSysSurfPlnMbrFeat\nAdvStructMember\nGusset\nWeldBeadFeat\nWeldCornerFeat\nWeldMemberFeat\nWeldmentFeature\nWeldmentTableFeat\nRound fillet corner\n".splitlines()
        if ItemValueA
    )
)






# keeps this focused behavior isolated so regressions remain immediately visible
def TestPCRTDD() -> None:
    WithoutBrep = ReadSldprt(KSample, include_brep=False)
    Expected = frozenset(
        {
            Capability.BODY_STRUCTURE,
            Capability.CONFIGURATIONS,
            Capability.EDITABLE_SKETCHES,
            Capability.PARAMETERS,
            Capability.PARAMETRIC_HISTORY,
            Capability.PROVENANCE,
            Capability.ROUNDTRIP_METADATA,
            Capability.SELECTIONS,
            Capability.SUPPORT_PLANES,
        }
    )
    assert WithoutBrep.capabilities == Expected
    WithBrep = ReadSldprt(KSample, include_brep=True)
    assert WithBrep.capabilities == Expected | {
        Capability.BREP,
        Capability.NATIVE_PAYLOADS,
    }






# keeps this focused behavior isolated so regressions remain immediately visible
def TestPSDDNDOIN() -> None:
    Archive = SldprtArchive.open(KSample)
    Streams = Archive.streams
    OriginalName = "Contents/Config-0-Partition"
    Streams["Contents/CustomerGeometryBlob"] = Streams.pop(OriginalName)
    Renamed = BuildSldprt(
        Streams,
        file_id=Archive.file_id,
        format_version=Archive.format_version,
        signatures=ContainerSignatures(KSample.read_bytes()),
    )
    Document = ReadSldprt(Renamed)
    assert len(Document.brep_payloads) == 3
    assert all((Payload.role == PayloadRole.BREP for Payload in Document.brep_payloads))
    assert (
        sum(
            (
                Payload.source_stream == "Contents/CustomerGeometryBlob"
                for Payload in Document.brep_payloads
            )
        )
        == 2
    )


















# keeps this focused behavior isolated so regressions remain immediately visible
def TestCDSDNRDTON() -> None:
    Archive = SldprtArchive.open(KSample)
    Keywords = Archive.require("swXmlContents/KeyWords").replace(
        b'Name="D1">&lt;MOD-DIAM&gt;5.5', b'Name="Diametre">5.5'
    )
    ModelDoc = DecodeNativeModel(
        Keywords, Archive.require("Contents/Config-0-ResolvedFeatures")
    )
    SketchA = next(
        (ItemValue for ItemValue in ModelDoc.sketches if ItemValue.object_id == 88)
    )
    assert SketchA.profiles[0].coordinates[2] == PytestLib.approx(2.75)
    assert SketchA.profiles[0].parameter_name == "Diametre"
    assert SketchA.profiles[0].dimension_kind == "diameter"
    assert SketchA.dimensions[0].kind == "diameter"
    assert SketchA.dimensions[0].native_offset is not None




# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not (KCorpus / "Engine_Block.SLDPRT").is_file(),
    reason="solidworks corpus is not present in this checkout",
)
def TestCHWFRTT() -> None:
    Document = ReadSldprt(KCorpus / "Engine_Block.SLDPRT", include_brep=False)
    Holes = [
        Feature
        for Feature in Document.feature_timeline
        if Feature.kind == FeatureKind.HOLE
    ]
    assert len(Holes) == 8
    assert {Feature.attributes["xml_tag"] for Feature in Holes} == {"HoleWizard"}
    assert all((Feature.attributes["native_type"] == "HoleWizard" for Feature in Holes))


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCRNS() -> None:
    Archive = SldprtArchive.open(KSample)
    assert Archive.file_id == 1901848975
    assert Archive.format_version == 4
    assert Archive.require("Contents/Config-0-ResolvedFeatures")
    assert b"<?xml" in Archive.require("swXmlContents/KeyWords")
    assert Archive.require("Contents/Config-0-Partition")


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCAVRSD() -> None:
    SourceDoc = bytearray(KSample.read_bytes())
    Original = SldprtArchive.from_bytes(SourceDoc)
    Replacement = bytes.fromhex("01020304")
    for RecordInfo in Original.records:
        SourceDoc[RecordInfo.offset + 6 : RecordInfo.offset + 10] = Replacement
    Recovered = SldprtArchive.from_bytes(SourceDoc)
    assert len(Recovered.records) == len(Original.records)
    assert {RecordInfo.signature[6:] for RecordInfo in Recovered.records} == {
        Replacement
    }
    assert Recovered.require("Contents/Config-0-ResolvedFeatures") == Original.require(
        "Contents/Config-0-ResolvedFeatures"
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARPHAB() -> None:
    Document = ReadSldprt(KSample)
    assert Document.validate() == ()
    assert len(Document.configurations) == 1
    assert len(Document.parameters) == 26
    assert len(Document.support_planes) == 7
    assert len(Document.sketches) == 5
    assert len(Document.feature_timeline) == 39
    assert len(Document.brep_payloads) == 3
    assert [Payload.kind for Payload in Document.brep_payloads] == [
        "partition",
        "partition",
        "deltas",
    ]
    assert [len(Payload.data or b"") for Payload in Document.brep_payloads] == [
        1513,
        30850,
        23150,
    ]
    assert (
        Document.brep_payloads[1].sha256
        == "3f3e3efbfbee0f41bda187579547881126cbf48101f006eecd759f491fc87ac6"
    )
    assert (
        Document.brep_payloads[2].sha256
        == "59d5eef7feb40d7a2ce52e20e50e14ca8eedaa1a1671b33a13fdc43720311cb7"
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARFOAD() -> None:
    Document = ReadSldprt(KSample, include_brep=False)
    Operations = {
        Feature.name: Feature
        for Feature in Document.feature_timeline
        if Feature.name
        in {
            "Boss-Extrude1",
            "Cut-Extrude1",
            "Boss-Extrude2",
            "Cut-Extrude2",
            "Boss-Extrude3",
            "Fillet1",
        }
    }
    assert Operations["Boss-Extrude1"].operation == BooleanOperation.JOIN
    assert Operations["Cut-Extrude1"].operation == BooleanOperation.CUT
    assert Operations["Boss-Extrude2"].operation == BooleanOperation.JOIN
    assert Operations["Cut-Extrude2"].operation == BooleanOperation.CUT
    assert Operations["Boss-Extrude3"].operation == BooleanOperation.JOIN
    BossOneDef = Operations["Boss-Extrude1"].definition
    CutOneDef = Operations["Cut-Extrude1"].definition
    BossTwoDef = Operations["Boss-Extrude2"].definition
    CutTwoDef = Operations["Cut-Extrude2"].definition
    BossThreeDef = Operations["Boss-Extrude3"].definition
    FilletOneDef = Operations["Fillet1"].definition
    assert isinstance(BossOneDef, ExtrusionFeature)
    assert isinstance(CutOneDef, ExtrusionFeature)
    assert isinstance(BossTwoDef, ExtrusionFeature)
    assert isinstance(CutTwoDef, ExtrusionFeature)
    assert isinstance(BossThreeDef, ExtrusionFeature)
    assert isinstance(FilletOneDef, FilletFeature)
    assert BossOneDef.length.value == 20.0
    assert CutOneDef.length.value == 0.25
    assert BossTwoDef.length.value == 0.75
    assert CutTwoDef.length.value == 9.0
    assert BossThreeDef.length.value == 6.0
    assert FilletOneDef.radius.value == 0.25
    assert Operations["Boss-Extrude1"].attributes["length_mm"] == 20.0
    assert Operations["Cut-Extrude1"].attributes["length_mm"] == 0.25
    assert Operations["Boss-Extrude2"].attributes["length_mm"] == 0.75
    assert Operations["Cut-Extrude2"].attributes["length_mm"] == 9.0
    assert Operations["Boss-Extrude3"].attributes["length_mm"] == 6.0
    assert Operations["Fillet1"].attributes["radius_mm"] == 0.25
    assert Operations["Fillet1"].selection_ids == ("sldprt:selection:116:edge:1",)
    assert Document.parameter("sldprt:parameter:88:D1").value.value == 5.5
    assert Document.parameter("sldprt:parameter:106:D1").value.value == 2.1


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARSFAP() -> None:
    Document = ReadSldprt(KSample, include_brep=False)
    PlaneTwo = Document.plane("sldprt:plane:62")
    assert PlaneTwo.transform.origin.x == PytestLib.approx(124.3)
    assert PlaneTwo.transform.x_axis.z == -1.0
    assert PlaneTwo.transform.y_axis.y == 1.0
    assert PlaneTwo.transform.z_axis.x == 1.0
    SketchOne = Document.sketch("sldprt:sketch:26")
    Profile = [
        Entity
        for Entity in SketchOne.entities
        if Entity.id in SketchOne.closed_profile_entity_ids[0]
    ]
    assert len(Profile) == 4
    assert isinstance(Profile[0].geometry, LineGeometry)
    assert Profile[0].geometry.start.x == PytestLib.approx(-124.3)
    assert Profile[0].geometry.start.y == PytestLib.approx(-89.75)
    SketchThree = Document.sketch("sldprt:sketch:63")
    assert len(SketchThree.closed_profile_entity_ids) == 3
    SketchFour = Document.sketch("sldprt:sketch:88")
    Circle = next(
        (
            Entity
            for Entity in SketchFour.entities
            if Entity.id == SketchFour.closed_profile_entity_ids[0][0]
        )
    )
    CircleInfo = Circle.geometry
    assert isinstance(CircleInfo, CircleGeometry)
    assert CircleInfo.center.x == PytestLib.approx(10.0)
    assert CircleInfo.center.y == PytestLib.approx(81.631746131982)
    assert CircleInfo.radius == PytestLib.approx(2.75)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARCGWG() -> None:
    Document = ReadSldprt(KSample, include_brep=False)
    ExpectedLineCounts = {
        "Sketch1": 2,
        "Sketch2": 2,
        "Sketch3": 6,
        "Sketch4": 1,
        "Sketch6": 2,
    }
    for SketchA in Document.sketches:
        Lines = [
            Entity.geometry
            for Entity in SketchA.entities
            if Entity.construction and isinstance(Entity.geometry, LineGeometry)
        ]
        assert len(Lines) == ExpectedLineCounts[SketchA.name]
    SketchOne = Document.sketch("sldprt:sketch:26")
    Diagonals = [
        Entity.geometry
        for Entity in SketchOne.entities
        if Entity.construction and isinstance(Entity.geometry, LineGeometry)
    ]
    assert {
        (LineInfo.start.x, LineInfo.start.y, LineInfo.end.x, LineInfo.end.y)
        for LineInfo in Diagonals
    } == {(124.3, 89.75, -124.3, -89.75), (124.3, -89.75, -124.3, 89.75)}
    SketchFour = Document.sketch("sldprt:sketch:88")
    Construction = [
        Entity.geometry
        for Entity in SketchFour.entities
        if Entity.construction and isinstance(Entity.geometry, LineGeometry)
    ]
    assert (
        Construction[0].start.x,
        Construction[0].start.y,
        Construction[0].end.x,
        Construction[0].end.y,
    ) == PytestLib.approx((10.0, 89.75, 10.0, -89.75))
    assert all(
        (
            not str(Constraint.kind).startswith("native_")
            for Constraint in SketchFour.constraints
        )
    )
    assert any(
        (isinstance(Entity.geometry, NativeGeometry) for Entity in SketchOne.entities)
    )
    SketchSix = Document.sketch("sldprt:sketch:106")
    assert any(
        (
            isinstance(Entity.geometry, NativeGeometry)
            and Entity.geometry.data.get("record_data")
            for Entity in SketchSix.entities
        )
    )


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not (KCorpus / "Cover.SLDPRT").is_file(),
    reason="solidworks corpus is not present in this checkout",
)
def TestAAPCP() -> None:
    Document = ReadSldprt(KCorpus / "Cover.SLDPRT", include_brep=False)
    SketchA = Document.sketch("sldprt:sketch:26")
    Entities = {Entity.id: Entity.geometry for Entity in SketchA.entities}
    ProfileGeometries = [
        Entities[Profile[0]] for Profile in SketchA.closed_profile_entity_ids
    ]
    ProfilesA = [
        Profile for Profile in ProfileGeometries if isinstance(Profile, CircleGeometry)
    ]
    assert len(ProfilesA) == len(ProfileGeometries)
    assert [Profile.radius for Profile in ProfilesA] == PytestLib.approx((16.0, 184.0))
    assert (ProfilesA[0].center.x, ProfilesA[0].center.y) == PytestLib.approx(
        (15.300876095409, 4.677947275564)
    )
    assert (ProfilesA[1].center.x, ProfilesA[1].center.y) == PytestLib.approx(
        (-130.107647738324, 130.107647738325)
    )


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not (KCorpus / "Cover.SLDPRT").is_file(),
    reason="solidworks corpus is not present in this checkout",
)
def TestABDOBMP() -> None:
    Document = ReadSldprt(KCorpus / "Cover.SLDPRT", include_brep=False)
    SketchA = Document.sketch("sldprt:sketch:77")
    ConstraintsA = {
        Constraint.parameter_id: Constraint
        for Constraint in SketchA.constraints
        if Constraint.parameter_id
    }
    assert tuple(
        (
            Reference.entity_id
            for Reference in ConstraintsA["sldprt:parameter:77:D2"].references
        )
    ) == ("sldprt:sketch:77:native:90347", "sldprt:sketch:77:native:87930")
    assert tuple(
        (
            Reference.entity_id
            for Reference in ConstraintsA["sldprt:parameter:77:D6"].references
        )
    ) == ("sldprt:sketch:77:native:87322", "sldprt:sketch:77:native:87484")
    Radial = Document.sketch("sldprt:sketch:27")
    RadialConstraints = {
        Constraint.parameter_id: Constraint
        for Constraint in Radial.constraints
        if Constraint.parameter_id
    }
    assert RadialConstraints["sldprt:parameter:27:D2"].references == ()


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not (KCorpus / "Engine_Block.SLDPRT").is_file(),
    reason="solidworks corpus is not present in this checkout",
)
def TestARLEBNMI() -> None:
    Document = ReadSldprt(KCorpus / "Engine_Block.SLDPRT", include_brep=False)
    SketchA = Document.sketch("sldprt:sketch:139")
    Expected = {
        145018: (
            (-98.287842584929, 161.92745289172),
            (-130.107647738324, 130.107647738326),
        ),
        145110: (
            (-130.107647738324, 130.107647738326),
            (-48.790367901871, 48.790367901872),
        ),
        145202: (
            (-48.790367901871, 48.790367901872),
            (-16.970562748477, 80.610173055267),
        ),
        145294: (
            (-16.970562748477, 80.610173055267),
            (-98.287842584929, 161.92745289172),
        ),
    }
    Entities: dict[int, SketchEntity] = {}
    for Entity in SketchA.entities:
        ProvenanceInfo = Entity.provenance
        assert ProvenanceInfo is not None
        assert ProvenanceInfo.spans
        Entities[ProvenanceInfo.spans[0].offset] = Entity
    for Offset, (Start, EndInfo) in Expected.items():
        Geometry = Entities[Offset].geometry
        assert isinstance(Geometry, LineGeometry)
        assert (Geometry.start.x, Geometry.start.y) == PytestLib.approx(Start)
        assert (Geometry.end.x, Geometry.end.y) == PytestLib.approx(EndInfo)












# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not (KCorpus / "Engine_Block.SLDPRT").is_file(),
    reason="solidworks corpus is not present in this checkout",
)
def TestAPULBRNI() -> None:
    Document = ReadSldprt(KCorpus / "Engine_Block.SLDPRT", include_brep=False)
    SketchA = Document.sketch("sldprt:sketch:200")
    Unknown = next(
        (
            Entity
            for Entity in SketchA.entities
            if Entity.provenance and Entity.provenance.spans[0].offset == 196708
        )
    )
    assert isinstance(Unknown.geometry, NativeGeometry)
    assert Unknown.geometry.data["locus"] == "03000300"
    assert Unknown.geometry.data["record_data"]
    Entity = next(
        (
            Entity
            for Entity in SketchA.entities
            if Entity.provenance and Entity.provenance.spans[0].offset == 198158
        )
    )
    assert isinstance(Entity.geometry, LineGeometry)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestEFWTSHAND() -> None:
    Document = ReadSldprt(KSample, include_brep=False)
    assert all(
        (Feature.definition is not None for Feature in Document.feature_timeline)
    )
    NativeA = [
        Feature.definition
        for Feature in Document.feature_timeline
        if isinstance(Feature.definition, NativeFeatureDefinition)
    ]
    assert NativeA
    assert all((Definition.type_id for Definition in NativeA))
    assert any((Definition.object_data["record_data"] for Definition in NativeA))




# keeps this focused behavior isolated so regressions remain immediately visible
def TestAAMARNJ() -> None:
    SourceDoc = KSample.read_bytes()
    Adapter = SldprtAdapter()
    assert Adapter.probe(SourceDoc).confidence == 1.0
    Document = ReadSldprt(SourceDoc, include_brep=False)
    Restored = CadDocument.from_json(Document.to_json())
    assert Restored.validate() == ()
    assert Restored.source.path == "<memory>"
    assert Restored.feature("sldprt:feature:116").name == "Fillet1"


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KCorpus.is_dir(),
    reason="the SOLIDWORKS corpus is not present in this checkout",
)
def TestELSCD() -> None:
    Examples = FilePath(__file__).resolve().parents[4] / "examples"
    Parts = sorted(
        (
            TargetPath
            for TargetPath in Examples.rglob("*")
            if TargetPath.is_file()
            and TargetPath.suffix.lower() == ".sldprt"
            and (not TargetPath.name.startswith("~$"))
        )
    )
    Documents = [ReadSldprt(TargetPath) for TargetPath in Parts]
    assert len(Parts) == 111
    assert all((Document.validate() == () for Document in Documents))
    assert sum((len(Document.brep_payloads) for Document in Documents)) == 909
    assert all(
        (
            Payload.role == PayloadRole.BREP
            for Document in Documents
            for Payload in Document.brep_payloads
        )
    )
    assert any(
        (
            not Payload.source_stream.endswith("Partition")
            for Document in Documents
            for Payload in Document.brep_payloads
        )
    )


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not (KCorpus / "Addons" / "Alternator.SLDPRT").is_file(),
    reason="solidworks corpus is not present in this checkout",
)
def TestAHPZPFV() -> None:
    Document = ReadSldprt(KCorpus / "Addons" / "Alternator.SLDPRT", include_brep=False)
    Plane = Document.plane("sldprt:plane:289")
    assert Plane.transform.origin.z == PytestLib.approx(50.0)
    assert Plane.transform.z_axis.z == 1.0
    assert Document.sketch("sldprt:sketch:292").support_plane_id == Plane.id
    assert Document.validate() == ()


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not (KCorpus / "Cylinder_heads" / "Spark_plug.SLDPRT").is_file(),
    reason="solidworks corpus is not present in this checkout",
)
def TestAAOITDD() -> None:
    Document = ReadSldprt(
        KCorpus / "Cylinder_heads" / "Spark_plug.SLDPRT", include_brep=False
    )
    assert Document.parameter("sldprt:parameter:107:D5").value.value == 2.0
    assert Document.parameter("sldprt:parameter:107:D5:2").value.value == 2.0
    assert Document.validate() == ()
