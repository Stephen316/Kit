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
from convert.adapters.solidworks.programs.configuration.revolve.pin.rightangle.Program import (
    EncodeProgram as EncodeConfig,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.rightangle.Program import (
    GetCoverage as GetConfigCoverage,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.rightangle.Program import (
    KReferenceDigest as KConfigDigest,
    KReferenceLength as KConfigLength,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.rightangle.Registry import (
    KConfigOps,
    KFieldOwners as KConfigOwners,
)
from convert.adapters.solidworks.programs.resolved.revolve.pin.rightangle.Program import (
    EncodeProgram,
    GetCoverage,
    KReferenceDigest,
    KReferenceLength,
)
from convert.adapters.solidworks.programs.resolved.revolve.pin.rightangle.Registry import (
    KFieldOwners,
    KResolvedOps,
)
from convert.adapters.solidworks.container.Format import (
    CONFIGURATION_STREAM as Stream,
    KIT_RESOLVED_STREAM as StreamA,
    RESOLVED_FEATURES_STREAM as StreamB,
)
from convert.adapters.solidworks.envelopes.revolve.pin.rightangle.Envelope import (
    BuildEnvelope,
    EncodeFeatures,
)

# centralizes shared evidence so every related assertion uses one value
KProfileMetres = (
    (0.0, -0.05),
    (0.0, 0.0),
    (0.0025, 0.0),
    (0.0025, -0.03),
    (0.0015, -0.02999),
    (0.0015, -0.05),
)

# centralizes shared evidence so every related assertion uses one value
KHeaderDigest = "9d146ad95cacd429338ca34ba74acb4b725ae8bce2c4d3018e99e3fcd4873880"

# centralizes shared evidence so every related assertion uses one value
KSourcePath = (
    FilePath(__file__).parents[4]
    / ".rescratch"
    / "sw"
    / "fcstd"
    / "kit_revolve_pin_top_90.FCStd"
)


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KSourcePath.is_file(),
    reason="top plane partial pin revolution corpus unavailable",
)
def TestPNZPWSCE(TmpPath: FilePath) -> None:
    SourceData = ReadFreecad(KSourcePath)
    TargetPath = TmpPath / "Pin90Public.SLDPRT"
    ResultData = WriteDocument(SourceData, TargetPath, allow_carrier=False)
    ArchiveData = SldprtArchive.open(TargetPath)
    EnvelopeData = BuildEnvelope()
    assert ResultData.IsVendorLoadable is True
    assert ResultData.IsAppUsable is True
    assert ResultData.IsNearLossless is True
    assert ResultData.MetadataMap["runtime"] == "python-stdlib"
    assert StreamA not in ArchiveData.streams
    assert ArchiveData.require(StreamB) == EncodeFeatures()
    assert ArchiveData.require(Stream) == EnvelopeData.Config0Payload
    assert (
        ArchiveData.require("Contents/Config-0-ModelHeader")
        == EnvelopeData.HeaderPayload
    )
    assert ArchiveData.require("Header2") == EnvelopeData.HeaderPayload


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPNZCPHETC() -> None:
    PayloadData = EncodeConfig()
    CoverageData = GetConfigCoverage()
    assert len(PayloadData) == KConfigLength == 24902
    assert Hashlib.sha256(PayloadData).hexdigest() == KConfigDigest
    assert CoverageData == {
        "stream_bytes": 24902,
        "typed": 24902,
        "opaque": 0,
        "accounted": 24902,
        "operations": 4297,
        "owners": 1058,
    }
    assert b"C:\\Users" not in PayloadData
    assert b".rescratch" not in PayloadData


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPNZCOTWG() -> None:
    CursorValue = 0
    for StartPos, FieldWidth, OwnerIndex, _, _ in KConfigOps:
        assert StartPos == CursorValue
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KConfigOwners)
        CursorValue += FieldWidth
    assert CursorValue == KConfigLength


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPNZPHETC() -> None:
    PayloadData = EncodeProgram()
    CoverageData = GetCoverage()
    assert len(PayloadData) == KReferenceLength == 12537
    assert Hashlib.sha256(PayloadData).hexdigest() == KReferenceDigest
    assert CoverageData == {
        "stream_bytes": 12537,
        "typed": 12537,
        "opaque": 0,
        "accounted": 12537,
        "operations": 3073,
        "owners": 506,
    }
    assert b"C:\\Users" not in PayloadData
    assert b".rescratch" not in PayloadData


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPNZPOTWG() -> None:
    CursorValue = 0
    AllowedKinds = {"definition", "classref", "objectref", "null", "string"}
    for StartPos, FieldWidth, OwnerIndex, KindName, _ in KResolvedOps:
        assert StartPos == CursorValue
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KFieldOwners)
        assert (
            KindName in AllowedKinds
            or KindName.startswith("primitive:")
            or KindName.startswith("direct:")
        )
        CursorValue += FieldWidth
    assert CursorValue == KReferenceLength
