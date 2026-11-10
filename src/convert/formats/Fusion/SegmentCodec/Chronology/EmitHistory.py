# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.formats.Fusion.SegmentCodec.Chronology.PackHistRefs import (
    PackHistRef,
    PackHistRefs,
)


# chronology order belongs to explicit record references rather than physical offsets
def EmitHistory(OwnerId: int, Entries: tuple[int, ...]) -> bytes:
    return bytes(6) + PackHistRef(OwnerId) + PackHistRefs(Entries)
