# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath


# path and memory inputs share the same bounded native archive contract
def LoadFusionBytes(SourceData: str | FilePath | bytes) -> tuple[bytes, str]:
    if isinstance(SourceData, bytes):
        return SourceData, ""
    SourcePath = FilePath(SourceData).expanduser().resolve()
    with SourcePath.open("rb") as SourceFile:
        DataValue = SourceFile.read(128 * 1024 * 1024 + 1)
    if len(DataValue) > 128 * 1024 * 1024:
        raise ValueError("Fusion ZIP exceeds input size limit")
    return DataValue, str(SourcePath)
