# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.geometry.models.VectorSpace import SpaceVector

# shared frame defaults stay precomputed constants so parameter defaults never call constructors
KOriginZero: SpaceVector = SpaceVector(0.0, 0.0, 0.0)

# world x direction stays precomputed so transform defaults never construct vectors
KAxisX: SpaceVector = SpaceVector(1.0, 0.0, 0.0)

# world y direction stays precomputed so transform defaults never construct vectors
KAxisY: SpaceVector = SpaceVector(0.0, 1.0, 0.0)

# world z direction stays precomputed so transform defaults never construct vectors
KAxisZ: SpaceVector = SpaceVector(0.0, 0.0, 1.0)


# orthogonal frames preserve placement without assuming one vendor coordinate convention
@ModelDataMut
class Transform(ModelBase):
    origin: SpaceVector = KOriginZero
    x_axis: SpaceVector = KAxisX
    y_axis: SpaceVector = KAxisY
    z_axis: SpaceVector = KAxisZ

    # anchor point keeps curve placement absolute without extra context
    @property
    def Origin(self) -> SpaceVector:
        return self.origin

    # basis column keeps frame math explicit for rotation sensitive code
    @property
    def XAxis(self) -> SpaceVector:
        return self.x_axis

    # basis column keeps frame math explicit for rotation sensitive code
    @property
    def YAxis(self) -> SpaceVector:
        return self.y_axis

    # basis column keeps frame math explicit for rotation sensitive code
    @property
    def ZAxis(self) -> SpaceVector:
        return self.z_axis


# one identity transform keeps placement defaults free of repeated constructor calls
KTransformIdentity: Transform = Transform()
