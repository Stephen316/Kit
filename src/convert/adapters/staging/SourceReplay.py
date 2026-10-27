# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from io import BytesIO as ByteStream
from io import StringIO as TextStream
from pathlib import Path as FilePath
from typing import Protocol
from typing import runtime_checkable as RuntimeCheck

from convert.adapters.base.ContractTypes import KSourceType


# replay detects reusable streams without requiring one shot receivers to support seeking
@RuntimeCheck
class ReplaySource(Protocol):

    # reusable streams need a concrete offset so probing can preserve caller state
    def tell(self) -> int:
        raise TypeError("replay sources require a concrete tell implementation")

    # reusable streams must restore their position before registry probing begins
    def seek(self, offset: int, whence: int = 0, /) -> int:
        raise TypeError("replay sources require a concrete seek implementation")


# probing must not consume one shot sources before the selected reader receives them
def GetReplayMut(SourceData: KSourceType) -> KSourceType:
    if isinstance(SourceData, (str, FilePath, bytes, bytearray)):
        return SourceData
    if isinstance(SourceData, ReplaySource):
        CanReplay = True
        try:
            StreamPos = SourceData.tell()
            _ = SourceData.seek(StreamPos)
        except (OSError, TypeError, ValueError):
            CanReplay = False
        if CanReplay:
            return SourceData
    SourceValue = SourceData.read()
    if isinstance(SourceValue, str):
        return TextStream(SourceValue)
    return ByteStream(SourceValue)
