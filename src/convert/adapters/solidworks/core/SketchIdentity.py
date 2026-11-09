# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


def AxisSourceId(KindValue: str, NativeId: int) -> str:
    return f"sldprt:{KindValue}:{NativeId}"


def MarkerId(NativeId: int, Offset: int) -> str:
    return f"sldprt:sketch:{NativeId}:native:{Offset}"
