# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from struct import pack as PackData

from pytest import raises as Raises

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.RecordSpan import RecordSpan


# synthetic class tables exercise ownership without shipping a donor payload
def IndexFixture(SecondOffset: int = 16) -> bytes:
    KindValue = b"FusionDesignSegmentType"
    KindField = PackData("<I", len(KindValue)) + KindValue
    return b"".join(
        (
            KindField,
            PackData("<IIIIII", 0, 0, 1234, 8, 0, 0),
            KindField,
            PackData("<IIII", 0, 1, 0, 2),
            PackData("<I", 4),
            b"Base",
            PackData("<IIII", 0, 0, 0, 0),
            PackData("<I", 5),
            b"Child",
            PackData("<I", 4),
            b"Base",
            PackData("<IIIQ", 0, 0, 1, 42),
            PackData("<IIQQIQQQII", 0, 1, 42, 0, 1, 42, SecondOffset, 43, 0, 0),
        )
    )


# payload boundaries must preserve both the primary and inherited record
def TestIndexSpans() -> None:
    BulkValue = (
        PackData("<I3sQ", 3, b"257", 42) + b"x" + PackData("<I3sQ", 3, b"256", 42)
    )
    assert ReadBulkSpans(BulkValue, IndexFixture()) == (
        RecordSpan(0, 15, 16, 42, 257, "Child", "", True),
        RecordSpan(16, 31, 31, 42, 256, "Base", "", False),
    )


# malformed offsets and independent bulk headers cannot override metadata ownership
def TestBadIndex() -> None:
    Primary = PackData("<I3sQ", 3, b"257", 42) + b"x"
    Continuation = PackData("<I3sQ", 3, b"256", 42)
    with Raises(ValueError, match="record extent"):
        _ = ReadBulkSpans(Primary + Continuation, IndexFixture(0))
    with Raises(ValueError, match="header and index disagree"):
        _ = ReadBulkSpans(Primary + PackData("<I3sQ", 3, b"257", 42), IndexFixture())
    with Raises(ValueError, match="header and index disagree"):
        _ = ReadBulkSpans(Primary + PackData("<I3sQ", 3, b"256", 43), IndexFixture())
    with Raises(ValueError, match="Truncated"):
        _ = ReadBulkSpans(Primary + Continuation, IndexFixture()[:-1])
