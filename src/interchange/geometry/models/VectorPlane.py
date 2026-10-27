# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from interchange.core.ModelBase import ModelBase, ModelDataMut


# planar vectors keep sketch coordinates distinct from spatial geometry
@ModelDataMut
class PlaneVector(ModelBase):
    x: float
    y: float

    # component access keeps vector math readable without tuple indexing
    @property
    def XCoord(self) -> float:
        return self.x

    # component access keeps vector math readable without tuple indexing
    @property
    def YCoord(self) -> float:
        return self.y
