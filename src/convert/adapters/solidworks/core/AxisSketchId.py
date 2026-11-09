# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import TYPE_CHECKING as TypeChecking
from convert.adapters.solidworks.resolved.Core import (
    REVOLUTION_AXIS_SKETCH as RevolutionAxisSketch,
)

if TypeChecking:
    from convert.adapters.solidworks.core.Native import NativeOperation


def AxisSketchId(Operation: NativeOperation) -> int | None:
    if Operation.axis_source_kind is None:
        return Operation.profile_id
    if Operation.axis_source_kind == RevolutionAxisSketch:
        return Operation.axis_source_id
    return None
