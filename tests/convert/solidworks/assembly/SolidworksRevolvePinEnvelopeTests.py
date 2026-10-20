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
from convert.adapters.solidworks.core.Native import (
    HeaderPayload,
    KHeaderObjects as Objects,
    KSolidworksConfigFlags as Flags,
    NativeIdentity,
)
from convert.adapters.solidworks.envelopes.revolve.pin.default.Envelope import (
    CalcPinBounds,
    EncodeConfig,
    EncodeHeader,
    GetCoverage,
    KConfigBytes,
    KConfigFields,
    KConfigOwners,
    KHeaderIdentity,
    KHeaderStamps,
    KHeaderUser,
)

# centralizes shared evidence so every related assertion uses one value
KFixtureRoot = (
    FilePath(__file__).resolve().parents[4]
    / "examples"
    / "Fixtures"
    / "SolidWorks"
    / "donors"
)

# centralizes shared evidence so every related assertion uses one value
KConfigDigest = "f5409831ddedb4c2c396e4b9485dc114acaf0d277e763edf35ac5daca1f0faf9"

# centralizes shared evidence so every related assertion uses one value
KHeaderDigest = "36335512255914fd6c84f47bb315368dfba48ab66dbee8b5c5195361f36f7d60"


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPCPHETC() -> None:
    PayloadData = EncodeConfig()
    CoverageData = GetCoverage()
    assert len(PayloadData) == KConfigBytes == 24902
    assert Hashlib.sha256(PayloadData).hexdigest() == KConfigDigest
    assert CoverageData == {
        "stream_bytes": 24902,
        "typed": 24902,
        "opaque": 0,
        "accounted": 24902,
        "operations": KConfigFields,
        "owners": KConfigOwners,
    }
    assert KConfigFields == 4297
    assert KConfigOwners == 1058
    assert b"C:\\Users" not in PayloadData
    assert b".rescratch" not in PayloadData


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPCPMCO() -> None:
    OracleData = (
        KFixtureRoot / "revolve_pin_top_full" / "container" / "Contents__Config-0.bin"
    ).read_bytes()
    assert EncodeConfig() == OracleData


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPMHMCO() -> None:
    CreatedStamp, ModifiedStamp, BaselineStamp, HeaderStamp = KHeaderIdentity
    IdentityData = NativeIdentity(
        CreatedStamp, ModifiedStamp, BaselineStamp, HeaderStamp, Flags, "Part1"
    )
    HeaderData = HeaderPayload(
        IdentityData,
        "Default",
        (*Objects, (26, "Sketch1", True), (31, "Revolve1", False)),
        "",
        KHeaderUser,
        32,
        {26: KHeaderStamps[0], 31: KHeaderStamps[1]},
        CalcPinBounds(),
    )
    OracleData = (
        KFixtureRoot
        / "revolve_pin_top_full"
        / "container"
        / "Contents__Config-0-ModelHeader.bin"
    ).read_bytes()
    assert len(HeaderData) == 2305
    assert Hashlib.sha256(HeaderData).hexdigest() == KHeaderDigest
    assert HeaderData == OracleData
    assert EncodeHeader() == OracleData
