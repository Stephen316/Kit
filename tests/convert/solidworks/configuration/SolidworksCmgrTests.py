# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from convert.adapters.solidworks.container.Cmgr import (
    RESIDUAL_SPANS as Spans,
    declared_opaque_split as DeclaredOpaqueSplit,
    tree_ids_for as TreeIdsFor,
)

# centralizes shared evidence so every related assertion uses one value
KBytesA = 1957

# centralizes shared evidence so every related assertion uses one value
KDigest = "96d8137fb0ea8d4f5f7eb9c159ec5434903ccde9aee55334dd1e1ed59243f44c"

# centralizes shared evidence so every related assertion uses one value
KBytesD = 2081

# centralizes shared evidence so every related assertion uses one value
KDigestA = "964995442cbf20936436d7ee4a38a5819b6bdb9a9071f740b31e8e2fca92a81d"

# centralizes shared evidence so every related assertion uses one value
KBytesC = 62

# centralizes shared evidence so every related assertion uses one value
KBytes = 1957

# centralizes shared evidence so every related assertion uses one value
KBytesB = 0

# centralizes shared evidence so every related assertion uses one value
KCount = 0

# centralizes shared evidence so every related assertion uses one value
KMmThree = (1476.0000000000002, 11954.000000000002)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestDAOBTTS() -> None:
    Split = DeclaredOpaqueSplit()
    assert Split["stream_bytes"] == KBytesA
    assert Split["declared"] == KBytes
    assert Split["opaque"] == KBytesB
    assert Split["residual_spans"] == KCount
    assert Split["declared"] + Split["opaque"] == Split["accounted"]
    assert Split["accounted"] == Split["stream_bytes"]


# keeps this focused behavior isolated so regressions remain immediately visible
def TestDGCIFTRZD() -> None:
    assert Spans == ()
    assert KBytesB == 0


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTSCEFC() -> None:
    for Features in (1, 4, 8):
        Split = DeclaredOpaqueSplit(feature_tree_ids=TreeIdsFor(Features))
        assert Split["opaque"] == 0
        assert Split["declared"] == Split["stream_bytes"]
