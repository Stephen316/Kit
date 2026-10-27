# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from typing import Protocol as TypeProtocol

from interchange.brep.validation.GeometryAccess import GeometryAccess
from interchange.brep.validation.TopologyAccess import TopologyAccess


# the validation view decouples topology storage from independent diagnostic passes
class BrepView(GeometryAccess, TopologyAccess, TypeProtocol):
    """combined diagnostic surface sharing one immutable topology snapshot"""
