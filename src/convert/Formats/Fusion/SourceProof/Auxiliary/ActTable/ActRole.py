from enum import StrEnum


# typed labels distinguish native change tokens from actual component properties
class ActRole(StrEnum):
    KAppearance = "Appearance"
    KGeometry = "Geometry"
    KPhysical = "PhysicalMaterial"
    KProperties = "Properties"
    KStructure = "StructureChange"
    KTransform = "Transform"
