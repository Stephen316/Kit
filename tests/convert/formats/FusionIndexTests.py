# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from struct import pack as Pack

from pytest import raises as Raises

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.RecordSpan import RecordSpan


# synthetic class tables exercise ownership without shipping a donor payload
def IndexFixture(SecondOffset: int = 16) -> bytes:
    KindValue = b"FusionDesignSegmentType"
    KindField = Pack("<I", len(KindValue)) + KindValue
    return b"".join(
        (
            KindField,
            Pack("<IIIIII", 0, 0, 1234, 8, 0, 0),
            KindField,
            Pack("<IIII", 0, 1, 0, 2),
            Pack("<I", 4),
            b"Base",
            Pack("<IIII", 0, 0, 0, 0),
            Pack("<I", 5),
            b"Child",
            Pack("<I", 4),
            b"Base",
            Pack("<IIIQ", 0, 0, 1, 42),
            Pack("<IIQQIQQQII", 0, 1, 42, 0, 1, 42, SecondOffset, 43, 0, 0),
        )
    )


# payload boundaries must preserve both the primary and inherited record
def TestIndexSpans() -> None:
    BulkValue = Pack("<I3sQ", 3, b"257", 42) + b"x" + Pack("<I3sQ", 3, b"256", 42)
    assert ReadBulkSpans(BulkValue, IndexFixture()) == (
        RecordSpan(0, 15, 16, 42, 257, "Child", "", True),
        RecordSpan(16, 31, 31, 42, 256, "Base", "", False),
    )


# malformed offsets and independent bulk headers cannot override metadata ownership
def TestBadIndex() -> None:
    Primary = Pack("<I3sQ", 3, b"257", 42) + b"x"
    Continuation = Pack("<I3sQ", 3, b"256", 42)
    with Raises(ValueError, match="record extent"):
        ReadBulkSpans(Primary + Continuation, IndexFixture(0))
    with Raises(ValueError, match="header and index disagree"):
        ReadBulkSpans(Primary + Pack("<I3sQ", 3, b"257", 42), IndexFixture())
    with Raises(ValueError, match="header and index disagree"):
        ReadBulkSpans(Primary + Pack("<I3sQ", 3, b"256", 43), IndexFixture())
    with Raises(ValueError, match="Truncated"):
        ReadBulkSpans(Primary + Continuation, IndexFixture()[:-1])
