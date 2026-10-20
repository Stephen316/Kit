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
from convert.adapters.solidworks.programs.configuration.revolve.pin.front.Program import (
    EncodeProgram as EncodeConfig,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.front.Program import (
    GetCoverage as GetConfigCoverage,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.front.Program import (
    KReferenceDigest as KConfigDigest,
    KReferenceLength as KConfigLength,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.front.Registry import (
    KConfigOps,
    KFieldOwners as KConfigOwners,
)
from convert.adapters.solidworks.programs.resolved.revolve.pin.front.Program import (
    EncodeProgram,
    GetCoverage,
    KReferenceDigest,
    KReferenceLength,
)
from convert.adapters.solidworks.programs.resolved.revolve.pin.front.Registry import (
    KFieldOwners,
    KResolvedOps,
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
KHeaderDigest = "6f7bd56fa6997638046a3013475af74469a90e115ae28ee3e338431bfb14820b"

# centralizes shared evidence so every related assertion uses one value
KSourcePath = (
    FilePath(__file__).parents[4]
    / ".rescratch"
    / "sw"
    / "fcstd"
    / "kit_revolve_pin_front.FCStd"
)


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KSourcePath.is_file(), reason="front plane pin revolution corpus unavailable"
)
def TestFPPWRFC(TmpPath: FilePath) -> None:
    SourceData = ReadFreecad(KSourcePath)
    with PytestLib.raises(ApplicationUsabilityError):
        _ = WriteDocument(
            SourceData, TmpPath / "FrontPinPending.SLDPRT", allow_carrier=False
        )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPCPHETC() -> None:
    PayloadData = EncodeConfig()
    CoverageData = GetConfigCoverage()
    assert len(PayloadData) == KConfigLength == 24976
    assert Hashlib.sha256(PayloadData).hexdigest() == KConfigDigest
    assert CoverageData == {
        "stream_bytes": 24976,
        "typed": 24976,
        "opaque": 0,
        "accounted": 24976,
        "operations": 4298,
        "owners": 1058,
    }
    assert b"C:\\Users" not in PayloadData
    assert b".rescratch" not in PayloadData


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPCOTWG() -> None:
    CursorValue = 0
    for StartPos, FieldWidth, OwnerIndex, _, _ in KConfigOps:
        assert StartPos == CursorValue
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KConfigOwners)
        CursorValue += FieldWidth
    assert CursorValue == KConfigLength


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPPHETC() -> None:
    PayloadData = EncodeProgram()
    CoverageData = GetCoverage()
    assert len(PayloadData) == KReferenceLength == 12265
    assert Hashlib.sha256(PayloadData).hexdigest() == KReferenceDigest
    assert CoverageData == {
        "stream_bytes": 12265,
        "typed": 12265,
        "opaque": 0,
        "accounted": 12265,
        "operations": 3005,
        "owners": 503,
    }
    assert b"C:\\Users" not in PayloadData
    assert b".rescratch" not in PayloadData


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPPOTWG() -> None:
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
