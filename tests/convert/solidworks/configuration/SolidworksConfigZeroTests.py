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
from convert.adapters.solidworks.configuration.ConfigZero import (
    CONFIG_FIELD_COUNT as Count,
    CONFIG_OPAQUE_BYTES as Bytes,
    CONFIG_OWNER_COUNT as CountA,
    REFERENCE_ATOM_ID as IdInfo,
    REFERENCE_LENGTH as Length,
    REFERENCE_TREE_ID as IdInfoA,
    declared_opaque_split as DeclaredOpaqueSplit,
    encode_config0_stream as EncodeConfigZeroStream,
)
from convert.adapters.solidworks.programs.configuration.default.Registry import (
    ConfigOps,
    FieldOwners,
)
from convert.adapters.solidworks.programs.configuration.box.Program import (
    EncodeProgram as EncodeBoxConfigProgram,
    ReferenceLength as BoxReferenceLength,
)
from convert.adapters.solidworks.programs.configuration.box.Registry import (
    ConfigOps as BoxConfigOps,
    FieldOwners as BoxFieldOwners,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError

# centralizes shared evidence so every related assertion uses one value
KBytes = 88

# centralizes shared evidence so every related assertion uses one value
KBytesA = 66


# keeps this focused behavior isolated so regressions remain immediately visible
def Atoms(FeatureCount: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        ((IdInfo + Index, IdInfoA + 8 * Index) for Index in range(FeatureCount))
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestERBHEOTO() -> None:
    SourceCursor = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, _ in ConfigOps:
        assert StartPos == SourceCursor
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(FieldOwners)
        assert KindName in {
            "definition",
            "classref",
            "objectref",
            "null",
            "string",
            "stringlist",
        } or KindName.startswith(("primitive:", "direct:"))
        assert "opaque" not in KindName
        assert "raw" not in KindName
        SourceCursor += FieldWidth
    assert SourceCursor == Length
    assert len(ConfigOps) == Count == 4341
    assert len(FieldOwners) == CountA == 1085


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/configuration/default/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestDBCIET() -> None:
    SourceCursor = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, _ in BoxConfigOps:
        assert StartPos == SourceCursor
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(BoxFieldOwners)
        assert "opaque" not in KindName.casefold()
        assert "raw" not in KindName.casefold()
        SourceCursor += FieldWidth
    assert SourceCursor == BoxReferenceLength == 25158
    assert len(EncodeBoxConfigProgram()) == BoxReferenceLength
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/configuration/box/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTVRPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/configuration/views/pair/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFVPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/configuration/fillet/views/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPVPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/configuration/pattern/views/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTFAFTEDS() -> None:
    SplitData = DeclaredOpaqueSplit(atoms=Atoms(3), part_name="TypedPart")
    assert SplitData["typed"] == SplitData["stream_bytes"]
    assert SplitData["accounted"] == SplitData["stream_bytes"]
    assert SplitData["opaque"] == Bytes == 0
    assert SplitData["operations"] == len(ConfigOps)
    assert SplitData["owners"] == len(FieldOwners)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCRPIR() -> None:
    with PytestLib.raises(SldprtFormatError, match="raw Config-0 prologue"):
        _ = EncodeConfigZeroStream(part_record_body=b"not allowed")
