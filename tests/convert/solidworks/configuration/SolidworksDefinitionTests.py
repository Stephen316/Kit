# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from pathlib import Path as FilePath
from convert.adapters.solidworks.container.Definition import (
    DRAFTING_STANDARDS as Standards,
    OPAQUE_SPANS as Spans,
    encode_body as EncodeBody,
)

# centralizes shared evidence so every related assertion uses one value
KBytesB = 3618

# centralizes shared evidence so every related assertion uses one value
KDigestA = "f5b20e1c8dbe0efece6a9d07f0806a0c8d051509a8c38431024e61986d887a9e"

# centralizes shared evidence so every related assertion uses one value
KUserInfo = "odin"

# centralizes shared evidence so every related assertion uses one value
KBytesC = 3618

# centralizes shared evidence so every related assertion uses one value
KBytesD = 0

# centralizes shared evidence so every related assertion uses one value
KSpans = 0

# centralizes shared evidence so every related assertion uses one value
KBytesA = 3736

# centralizes shared evidence so every related assertion uses one value
KDigest = "7479a6640fa3647a4801f41bc2bd1cc4a08c845620fc0a4412dd2aa407aadf19"

# centralizes shared evidence so every related assertion uses one value
KOffset = 20

# centralizes shared evidence so every related assertion uses one value
KBytes = 16

# centralizes shared evidence so every related assertion uses one value
KBytesE = 72

# centralizes shared evidence so every related assertion uses one value
KViewInfo = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestDBCTCB() -> None:
    Opaque = sum((len(SpanInfo) for SpanInfo in Spans))
    assert len(Spans) == KSpans
    assert Opaque == KBytesD
    assert KBytesC + Opaque == KBytesB
    Encoded = EncodeBody(standard=Standards[0], user=KUserInfo)
    assert len(Encoded) - Opaque == KBytesC


# keeps this focused behavior isolated so regressions remain immediately visible
def TestDWCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/container/Definition.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "OPAQUE_SPANS = (" not in SourceText
