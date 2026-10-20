# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import hashlib as Hashlib
from pathlib import Path as FilePath
import pytest as PytestLib
from convert import write_document as WriteDocument
from convert.adapters.freecad import read_freecad as ReadFreecad
from convert.adapters.solidworks.container.Container import (
    SldprtArchive,
)
from convert.adapters.solidworks.container.Format import (
    KIT_RESOLVED_STREAM as Stream,
    RESOLVED_FEATURES_STREAM as StreamA,
)
from convert.adapters.solidworks.resolved.Core import (
    locate_features as LocateFeatures,
)
from convert.adapters.solidworks.programs.resolved.boss.cut.circle.Program import (
    EncodeProgram,
)
from convert.adapters.solidworks.programs.resolved.boss.cut.circle.Registry import (
    KFieldOwners,
    KResolvedOps,
)

# centralizes shared evidence so every related assertion uses one value
KRepoRoot = FilePath(__file__).resolve().parents[4]

# centralizes shared evidence so every related assertion uses one value
KOracleStream = (
    KRepoRoot
    / "examples"
    / "Fixtures"
    / "SolidWorks"
    / "donors"
    / "boss_cut_cut_blind"
    / "resolved.bin"
)

# centralizes shared evidence so every related assertion uses one value
KSourcePath = (
    KRepoRoot / ".rescratch" / "gates" / "fcstd" / "gate_boss_cut_circle.FCStd"
)

# centralizes shared evidence so every related assertion uses one value
KProgramDigest = "ea2e72fee693b357d6ccea3aac0f9a64a428f5b851aff0d77faf422491d939a6"


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KSourcePath.is_file(),
    reason="boss plus rectangular and circular blind-cut corpus unavailable",
)
def TestBCCPWSTP(TmpPath: FilePath) -> None:
    SourceData = ReadFreecad(KSourcePath)
    TargetPath = TmpPath / "BossCutCirclePublic.SLDPRT"
    ResultData = WriteDocument(SourceData, TargetPath, allow_carrier=False)
    ArchiveData = SldprtArchive.open(TargetPath)
    FeatureData = LocateFeatures(ArchiveData.require(StreamA))
    assert ResultData.IsVendorLoadable is True
    assert ResultData.IsAppUsable is True
    assert ResultData.IsNearLossless is True
    assert ResultData.MetadataMap["runtime"] == "python-stdlib"
    assert Stream not in ArchiveData.streams
    assert tuple((ItemData.name for ItemData in FeatureData)) == (
        "Boss-Extrude1",
        "Cut-Extrude1",
        "Cut-Extrude2",
    )
    assert tuple((ItemData.depth_mm for ItemData in FeatureData)) == PytestLib.approx(
        (15.0, 5.0, 9.0)
    )
    assert tuple((ItemData.reversed for ItemData in FeatureData)) == (
        True,
        False,
        False,
    )
    assert FeatureData[0].bounds_mm == PytestLib.approx((-30.0, -20.0, 30.0, 20.0))
    assert FeatureData[1].bounds_mm == PytestLib.approx((-24.0, -4.0, 24.0, 4.0))
    assert FeatureData[2].arcs[0].centre_mm == PytestLib.approx((0.0, 12.0))
    assert FeatureData[2].arcs[0].radius_mm == PytestLib.approx(6.0)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBCCPCETF() -> None:
    PayloadData = EncodeProgram()
    assert len(PayloadData) == 21021
    assert Hashlib.sha256(PayloadData).hexdigest() == KProgramDigest
    assert PayloadData == KOracleStream.read_bytes()
    assert len(KResolvedOps) == 5302
    assert len(KFieldOwners) == 520
    CursorPos = 0
    ObjectCount = 0
    DefineCount = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, _ in KResolvedOps:
        assert StartPos == CursorPos
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KFieldOwners)
        assert KindName in {
            "definition",
            "classref",
            "objectref",
            "null",
            "string",
        } or KindName.startswith(("primitive:", "direct:"))
        ObjectCount += KindName in {"definition", "classref", "objectref", "null"}
        DefineCount += KindName == "definition"
        CursorPos += FieldWidth
    assert CursorPos == len(PayloadData)
    assert ObjectCount == 734
    assert DefineCount == 46


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBCCPCNVB() -> None:
    ProgramPath = (
        KRepoRoot
        / "src"
        / "convert"
        / "adapters"
        / "solidworks"
        / "programs"
        / "resolved"
        / "boss"
        / "cut"
        / "circle"
        / "Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()
    assert ".rescratch" not in SourceText
    assert "examples/Fixtures/SolidWorks/donors" not in SourceText
