# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector

# explicit facade exports preserve historical imports while keeping ownership discoverable
__all__ = ["BoundingBox", "PlaneVector", "SpaceVector", "Transform"]
