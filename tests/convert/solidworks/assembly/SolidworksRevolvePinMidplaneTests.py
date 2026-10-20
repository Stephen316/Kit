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
from convert import ApplicationUsabilityError, write_document as WriteDocument
from convert.adapters.freecad import read_freecad as ReadFreecad
from convert.adapters.solidworks.programs.configuration.revolve.pin.midplane.Program import (
    EncodeProgram as EncodeConfig,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.midplane.Program import (
    GetCoverage as GetConfigCoverage,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.midplane.Program import (
    KReferenceDigest as KConfigDigest,
    KReferenceLength as KConfigLength,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.midplane.Registry import (
    KConfigOps,
    KFieldOwners as KConfigOwners,
)
from convert.adapters.solidworks.container.Container import (
    SldprtArchive,
)
from convert.adapters.solidworks.container.Format import (
    CONFIGURATION_STREAM as Stream,
    RESOLVED_FEATURES_STREAM as StreamA,
)
from convert.adapters.solidworks.programs.resolved.revolve.pin.midplane.Program import (
    EncodeProgram,
    GetCoverage,
    KReferenceDigest,
    KReferenceLength,
)
from convert.adapters.solidworks.programs.resolved.revolve.pin.midplane.Registry import (
    KFieldOwners,
    KResolvedOps,
)
from convert.adapters.solidworks.envelopes.revolve.pin.midplane.Envelope import (
    EncodeHeader,
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
KHeaderDigest = "4cb455532120074010565342eab6df3b83df1bf45ad0c25bf391664790de07ca"

# centralizes shared evidence so every related assertion uses one value
KSourcePath = (
    FilePath(__file__).parents[4]
    / ".rescratch"
    / "sw"
    / "fcstd"
    / "kit_revolve_pin_top_midplane.FCStd"
)

# centralizes shared evidence so every related assertion uses one value
KOraclePath = (
    FilePath(__file__).parents[4]
    / ".rescratch"
    / "revolve_pin_midplane"
    / "revolve_pin_top_midplane.oracle.SLDPRT"
)


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KSourcePath.is_file(),
    reason="top plane symmetric pin revolution corpus unavailable",
)
def TestMPPWRFC(TmpPath: FilePath) -> None:
    SourceData = ReadFreecad(KSourcePath)
    with PytestLib.raises(ApplicationUsabilityError):
        _ = WriteDocument(
            SourceData, TmpPath / "MidplanePinPending.SLDPRT", allow_carrier=False
        )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMPCPHETC() -> None:
    PayloadData = EncodeConfig()
    assert len(PayloadData) == KConfigLength == 24902
    assert Hashlib.sha256(PayloadData).hexdigest() == KConfigDigest
    assert GetConfigCoverage() == {
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
def TestMPCOTWG() -> None:
    CursorValue = 0
    for StartPos, FieldWidth, OwnerIndex, _, _ in KConfigOps:
        assert StartPos == CursorValue
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KConfigOwners)
        CursorValue += FieldWidth
    assert CursorValue == KConfigLength


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMPPHETC() -> None:
    PayloadData = EncodeProgram()
    assert len(PayloadData) == KReferenceLength == 14065
    assert Hashlib.sha256(PayloadData).hexdigest() == KReferenceDigest
    assert GetCoverage() == {
        "stream_bytes": 14065,
        "typed": 14065,
        "opaque": 0,
        "accounted": 14065,
        "operations": 3374,
        "owners": 506,
    }
    assert b"C:\\Users" not in PayloadData
    assert b".rescratch" not in PayloadData


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMPPOTWG() -> None:
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


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(not KOraclePath.is_file(), reason="midplane oracle unavailable")
def TestMPPMLO() -> None:
    ArchiveData = SldprtArchive.open(KOraclePath)
    assert ArchiveData.require(Stream) == EncodeConfig()
    assert ArchiveData.require(StreamA) == EncodeProgram()
    assert ArchiveData.require("Contents/Config-0-ModelHeader") == EncodeHeader()
    assert ArchiveData.require("Header2") == EncodeHeader()
