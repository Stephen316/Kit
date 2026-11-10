# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from enum import StrEnum


# typed labels distinguish native change tokens from actual component properties
class ActRole(StrEnum):
    KAppearance = "Appearance"
    KGeometry = "Geometry"
    KPhysical = "PhysicalMaterial"
    KProperties = "Properties"
    KStructure = "StructureChange"
    KTransform = "Transform"
