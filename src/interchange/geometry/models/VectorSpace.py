from interchange.core.ModelBase import ModelBase, ModelDataMut


# spatial vectors give every geometry subsystem one coordinate contract
@ModelDataMut
class SpaceVector(ModelBase):
    x: float
    y: float
    z: float

    # component access keeps vector math readable without tuple indexing
    @property
    def XCoord(self) -> float:
        return self.x

    # component access keeps vector math readable without tuple indexing
    @property
    def YCoord(self) -> float:
        return self.y

    # component access keeps vector math readable without tuple indexing
    @property
    def ZCoord(self) -> float:
        return self.z
